import { useEffect, useMemo, useRef, useState } from "react";
import type { LabelPatch, PhotoDetail, PhotoListItem } from "@mybestphotos/shared";
import { DetailPane } from "./ui/components/DetailPane";
import { FiltersPane } from "./ui/components/FiltersPane";
import { MapPlaceholder } from "./ui/components/MapPlaceholder";
import { PhotoGrid } from "./ui/components/PhotoGrid";
import { SettingsView } from "./ui/components/SettingsView";
import { TimelineView } from "./ui/components/TimelineView";
import { TopBar } from "./ui/components/TopBar";
import { getJson } from "./ui/lib/api";
import { FALLBACK_DETAIL, FALLBACK_ITEMS } from "./ui/lib/fallbackData";
import { getSelectedTags, reconcileSelection, statusFromItem } from "./ui/lib/utils";
import type { FacetsResponse, PhotoListResponse, SettingsState, ViewMode } from "./ui/types";

const API_BASE = import.meta.env.VITE_API_BASE || "/api/v1";

export default function App() {
  const [viewMode, setViewMode] = useState<ViewMode>("browse");
  const [items, setItems] = useState<PhotoListItem[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [detail, setDetail] = useState<PhotoDetail | null>(null);

  const [search, setSearch] = useState("");
  const [minScore, setMinScore] = useState(0.6);
  const [status, setStatus] = useState("all");
  const [cameraMake, setCameraMake] = useState("");
  const [cameraModel, setCameraModel] = useState("");
  const [category, setCategory] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");

  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [hasMore, setHasMore] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const [facets, setFacets] = useState<FacetsResponse>({ camera: [], categories: [] });
  const [stubActive, setStubActive] = useState(false);
  const [settings, setSettings] = useState<SettingsState>({
    showScores: true,
    compactCards: false,
    autoplayDetailPreview: true,
    density: "comfortable",
  });

  const pageSize = 60;
  const loadMoreRef = useRef<HTMLDivElement>(null);

  const queryString = useMemo(() => {
    const params = new URLSearchParams();
    if (search.trim()) params.set("q", search.trim());
    if (cameraMake) params.set("cameraMake", cameraMake);
    if (cameraModel) params.set("cameraModel", cameraModel);
    if (category) params.set("category", category);
    if (dateFrom) params.set("dateFrom", `${dateFrom}T00:00:00.000Z`);
    if (dateTo) params.set("dateTo", `${dateTo}T23:59:59.999Z`);
    params.set("minPrintScore12x18", String(minScore));
    params.set("status", status);
    params.set("page", String(page));
    params.set("pageSize", String(pageSize));
    params.set("sort", "curation_desc");
    return params.toString();
  }, [search, cameraMake, cameraModel, category, dateFrom, dateTo, minScore, status, page]);

  useEffect(() => {
    setPage(1);
  }, [search, cameraMake, cameraModel, category, dateFrom, dateTo, minScore, status]);

  useEffect(() => {
    if (stubActive) return;
    void getJson<FacetsResponse>(`${API_BASE}/facets`)
      .then(setFacets)
      .catch(() => setFacets({ camera: [], categories: [] }));
  }, [stubActive]);

  useEffect(() => {
    let cancelled = false;

    async function loadList() {
      setIsLoading(true);
      try {
        const data = await getJson<PhotoListResponse>(`${API_BASE}/photos?${queryString}`);
        if (cancelled) return;

        setStubActive(false);
        setItems((previousItems) => {
          const mergedItems = page === 1 ? data.items : [...previousItems, ...data.items];
          setSelectedId((previousSelected) => reconcileSelection(mergedItems, previousSelected));
          return mergedItems;
        });
        setTotal(data.total ?? data.items.length);
        setHasMore(Boolean(data.hasMore));
      } catch {
        if (cancelled) return;

        setStubActive(true);
        setItems(FALLBACK_ITEMS);
        setSelectedId(1);
        setTotal(FALLBACK_ITEMS.length);
        setHasMore(false);
      } finally {
        if (!cancelled) setIsLoading(false);
      }
    }

    void loadList();
    return () => {
      cancelled = true;
    };
  }, [queryString, page]);

  useEffect(() => {
    if (!selectedId) {
      setDetail(null);
      return;
    }

    if (stubActive) {
      setDetail(FALLBACK_DETAIL);
      return;
    }

    void getJson<PhotoDetail>(`${API_BASE}/photos/${selectedId}`)
      .then(setDetail)
      .catch(() => {
        setStubActive(true);
        setDetail(FALLBACK_DETAIL);
      });
  }, [selectedId, stubActive]);

  useEffect(() => {
    const sentinel = loadMoreRef.current;
    if (!sentinel || !hasMore) return;

    const observer = new IntersectionObserver(
      (entries) => {
        const [entry] = entries;
        if (entry?.isIntersecting && !isLoading) setPage((previous) => previous + 1);
      },
      { rootMargin: "300px 0px" },
    );

    observer.observe(sentinel);
    return () => observer.disconnect();
  }, [hasMore, isLoading]);

  async function patchLabels(payload: LabelPatch) {
    if (!selectedId) return;
    if (stubActive && detail) {
      setDetail({ ...detail, labels: { ...detail.labels, ...payload } });
      return;
    }

    await fetch(`${API_BASE}/photos/${selectedId}/labels`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    await Promise.all([
      getJson<PhotoListResponse>(`${API_BASE}/photos?${queryString}`).then((data) => {
        setItems(data.items);
        setSelectedId((previousSelected) => reconcileSelection(data.items, previousSelected));
      }),
      getJson<PhotoDetail>(`${API_BASE}/photos/${selectedId}`).then(setDetail),
    ]);
  }

  const cameraMakeOptions = Array.from(
    new Set(facets.camera.map((row) => row.camera_make).filter((row): row is string => Boolean(row))),
  );

  const cameraModelOptions = Array.from(
    new Set(
      facets.camera
        .filter((row) => (cameraMake ? row.camera_make === cameraMake : true))
        .map((row) => row.camera_model)
        .filter((row): row is string => Boolean(row)),
    ),
  );

  const statusSummary = useMemo(() => {
    const summary = { all: items.length, keep: 0, favorite: 0, reject: 0, unreviewed: 0 };
    for (const item of items) summary[statusFromItem(item)] += 1;
    return summary;
  }, [items]);

  const timelineGroups = useMemo(() => {
    const grouped = new Map<string, PhotoListItem[]>();
    for (const item of items) {
      const date = item.photoTakenAt ? new Date(item.photoTakenAt) : null;
      const year = date ? String(date.getFullYear()) : "Unknown";
      const bucket = grouped.get(year) || [];
      bucket.push(item);
      grouped.set(year, bucket);
    }

    return [...grouped.entries()]
      .sort((a, b) => Number(b[0]) - Number(a[0]))
      .map(([year, yearItems]) => ({ year, count: yearItems.length, items: yearItems.slice(0, 5) }));
  }, [items]);

  const selectedTags = useMemo(() => getSelectedTags(detail), [detail]);

  function resetFilters() {
    setStatus("all");
    setCategory("");
    setCameraMake("");
    setCameraModel("");
    setDateFrom("");
    setDateTo("");
    setMinScore(0.6);
  }

  return (
    <div className="shell">
      <TopBar viewMode={viewMode} search={search} onSearchChange={setSearch} onViewModeChange={setViewMode} />
      {stubActive && <div className="banner">Stub mode active: API unavailable, showing sample data.</div>}

      {viewMode === "timeline" && (
        <TimelineView
          itemsCount={items.length}
          groups={timelineGroups}
          apiBase={API_BASE}
          onSelectPhoto={setSelectedId}
          onJumpToBrowse={() => setViewMode("browse")}
        />
      )}

      {viewMode === "map" && <MapPlaceholder />}

      {viewMode === "settings" && <SettingsView settings={settings} onSettingsChange={setSettings} />}

      {viewMode === "browse" && (
        <div className="layout">
          <FiltersPane
            status={status}
            category={category}
            cameraMake={cameraMake}
            cameraModel={cameraModel}
            dateFrom={dateFrom}
            dateTo={dateTo}
            minScore={minScore}
            facets={facets}
            cameraMakeOptions={cameraMakeOptions}
            cameraModelOptions={cameraModelOptions}
            onStatusChange={setStatus}
            onCategoryChange={setCategory}
            onCameraMakeChange={(value) => {
              setCameraMake(value);
              setCameraModel("");
            }}
            onCameraModelChange={setCameraModel}
            onDateFromChange={setDateFrom}
            onDateToChange={setDateTo}
            onMinScoreChange={setMinScore}
            onReset={resetFilters}
          />

          <PhotoGrid
            items={items}
            selectedId={selectedId}
            status={status}
            total={total}
            isLoading={isLoading}
            hasMore={hasMore}
            settings={settings}
            statusSummary={statusSummary}
            apiBase={API_BASE}
            loadMoreRef={loadMoreRef}
            onSelectPhoto={setSelectedId}
            onStatusChange={setStatus}
          />

          <DetailPane
            detail={detail}
            selectedTags={selectedTags}
            apiBase={API_BASE}
            onPatchLabels={patchLabels}
            onNotesChange={(notes) => {
              if (!detail) return;
              setDetail({ ...detail, labels: { ...detail.labels, notes } });
            }}
          />
        </div>
      )}
    </div>
  );
}
