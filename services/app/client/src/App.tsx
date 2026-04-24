import { useEffect, useMemo, useRef, useState } from "react";
import type { LabelPatch, PhotoDetail, PhotoListItem } from "@mybestphotos/shared";
import { DetailPane } from "./ui/components/DetailPane";
import { FiltersPane } from "./ui/components/FiltersPane";
import { PhotoGrid } from "./ui/components/PhotoGrid";
import { TimelineView } from "./ui/components/TimelineView";
import { TopBar } from "./ui/components/TopBar";
import { getJson } from "./ui/lib/api";
import { FALLBACK_DETAIL, FALLBACK_ITEMS } from "./ui/lib/fallbackData";
import { getSelectedTags, reconcileSelection } from "./ui/lib/utils";
import type { FacetsResponse, PhotoListResponse, StatusSummaryResponse, ViewMode } from "./ui/types";

const API_BASE = import.meta.env.VITE_API_BASE || "/api/v1";

export default function App() {
  const [viewMode, setViewMode] = useState<ViewMode>("browse");
  const [items, setItems] = useState<PhotoListItem[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [detail, setDetail] = useState<PhotoDetail | null>(null);

  const [search, setSearch] = useState("");
  const [minScore, setMinScore] = useState(0.6);
  const [maxScore, setMaxScore] = useState(1);
  const [status, setStatus] = useState("all");
  const [cameraMake, setCameraMake] = useState("");
  const [cameraModel, setCameraModel] = useState("");
  const [category, setCategory] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [dateBounds, setDateBounds] = useState<{ min: string; max: string }>({ min: "", max: "" });
  const [notesDraft, setNotesDraft] = useState("");

  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [hasMore, setHasMore] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [statusSummary, setStatusSummary] = useState<StatusSummaryResponse>({ all: 0, favorite: 0, hidden: 0, unreviewed: 0 });

  const [facets, setFacets] = useState<FacetsResponse>({ camera: [], categories: [], dateBounds: { min: null, max: null } });
  const [stubActive, setStubActive] = useState(false);
  const [filtersCollapsed, setFiltersCollapsed] = useState(false);
  const [filtersHovered, setFiltersHovered] = useState(false);

  const [sort, setSort] = useState<string>("aesthetic_desc");
  const [iconScale, setIconScale] = useState(1);

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
    params.set("maxPrintScore12x18", String(maxScore));
    params.set("status", status);
    params.set("page", String(page));
    params.set("pageSize", String(pageSize));
    params.set("sort", sort);
    return params.toString();
  }, [search, cameraMake, cameraModel, category, dateFrom, dateTo, minScore, maxScore, status, page, sort]);

  const summaryQueryString = useMemo(() => {
    const params = new URLSearchParams();
    if (search.trim()) params.set("q", search.trim());
    if (cameraMake) params.set("cameraMake", cameraMake);
    if (cameraModel) params.set("cameraModel", cameraModel);
    if (category) params.set("category", category);
    if (dateFrom) params.set("dateFrom", `${dateFrom}T00:00:00.000Z`);
    if (dateTo) params.set("dateTo", `${dateTo}T23:59:59.999Z`);
    params.set("minPrintScore12x18", String(minScore));
    params.set("maxPrintScore12x18", String(maxScore));
    return params.toString();
  }, [search, cameraMake, cameraModel, category, dateFrom, dateTo, minScore, maxScore]);


  useEffect(() => {
    setPage(1);
  }, [search, cameraMake, cameraModel, category, dateFrom, dateTo, minScore, maxScore, status, sort]);

  useEffect(() => {
    if (stubActive) return;
    void getJson<FacetsResponse>(`${API_BASE}/facets`)
      .then((response) => {
        setFacets(response);
        const nextMin = response.dateBounds?.min ?? "";
        const nextMax = response.dateBounds?.max ?? "";
        setDateBounds({ min: nextMin, max: nextMax });
        setDateFrom((previous) => previous || nextMin);
        setDateTo((previous) => previous || nextMax);
      })
      .catch(() => setFacets({ camera: [], categories: [], dateBounds: { min: null, max: null } }));
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
      setNotesDraft("");
      return;
    }

    if (stubActive) {
      setDetail(FALLBACK_DETAIL);
      setNotesDraft(FALLBACK_DETAIL.labels.notes || "");
      return;
    }

    void getJson<PhotoDetail>(`${API_BASE}/photos/${selectedId}`)
      .then((photoDetail) => {
        setDetail(photoDetail);
        setNotesDraft(photoDetail.labels.notes || "");
      })
      .catch(() => {
        setStubActive(true);
        setDetail(FALLBACK_DETAIL);
        setNotesDraft(FALLBACK_DETAIL.labels.notes || "");
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

  async function patchLabelsForPhoto(photoId: number, payload: LabelPatch) {
    if (stubActive && detail && selectedId === photoId) {
      setDetail({ ...detail, labels: { ...detail.labels, ...payload } });
      return;
    }

    await fetch(`${API_BASE}/photos/${photoId}/labels`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    setItems((previousItems) => {
      const patchedItems = previousItems
        .map((item) => (item.id === photoId
          ? {
              ...item,
              keepFlag: payload.keepFlag === undefined ? item.keepFlag : payload.keepFlag,
              rejectFlag: payload.rejectFlag === undefined ? item.rejectFlag : payload.rejectFlag,
              favoriteFlag: payload.favoriteFlag === undefined ? item.favoriteFlag : payload.favoriteFlag,
            }
          : item))
        .filter((item) => {
          if (status === "all") return item.rejectFlag !== true;
          if (status === "favorite") return item.favoriteFlag === true && item.rejectFlag !== true;
          if (status === "hidden") return item.rejectFlag === true;
          if (status === "unreviewed") {
            return item.rejectFlag !== true && item.favoriteFlag !== true && item.keepFlag !== true;
          }
          return true;
        });

      setSelectedId((previousSelected) => reconcileSelection(patchedItems, previousSelected));
      return patchedItems;
    });

    setDetail((previousDetail) => {
      if (!previousDetail || previousDetail.id !== photoId) return previousDetail;
      return {
        ...previousDetail,
        labels: {
          ...previousDetail.labels,
          ...payload,
        },
      };
    });

    if (!stubActive) {
      void getJson<StatusSummaryResponse>(`${API_BASE}/photos/status-summary?${summaryQueryString}`)
        .then((response) => setStatusSummary(response))
        .catch(() => undefined);
    }
  }

  async function patchLabels(payload: LabelPatch) {
    if (!selectedId) return;
    await patchLabelsForPhoto(selectedId, payload);
  }

  async function saveNotes() {
    if (!detail) return;
    await patchLabels({ notes: notesDraft });
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



  useEffect(() => {
    if (stubActive) {
      const fallbackSummary = {
        all: FALLBACK_ITEMS.filter((item) => item.rejectFlag !== true).length,
        favorite: FALLBACK_ITEMS.filter((item) => item.favoriteFlag === true && item.rejectFlag !== true).length,
        hidden: FALLBACK_ITEMS.filter((item) => item.rejectFlag === true).length,
        unreviewed: FALLBACK_ITEMS.filter((item) => !item.keepFlag && !item.favoriteFlag && !item.rejectFlag).length,
      };
      setStatusSummary(fallbackSummary);
      return;
    }

    void getJson<StatusSummaryResponse>(`${API_BASE}/photos/status-summary?${summaryQueryString}`)
      .then((response) => setStatusSummary(response))
      .catch(() => {
        const fallbackSummary = { all: 0, favorite: 0, hidden: 0, unreviewed: 0 };
        setStatusSummary(fallbackSummary);
      });
  }, [summaryQueryString, stubActive]);

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
  const filtersFullyCollapsed = filtersCollapsed && !filtersHovered;

  function resetFilters() {
    setStatus("all");
    setCategory("");
    setCameraMake("");
    setCameraModel("");
    setDateFrom(dateBounds.min);
    setDateTo(dateBounds.max);
    setMinScore(0.6);
    setMaxScore(1);
  }

  return (
    <div className="shell">
      <TopBar viewMode={viewMode} search={search} onSearchChange={setSearch} onViewModeChange={setViewMode} />
      {stubActive && <div className="banner">Stub mode active: API unavailable, showing sample data.</div>}

      {viewMode === "timeline" && (
        <div className={`layout timeline-layout ${filtersFullyCollapsed ? "filters-collapsed" : ""}`}>
          <FiltersPane
            isCollapsed={filtersCollapsed}
            isHovered={filtersHovered}
            status={status}
            category={category}
            cameraMake={cameraMake}
            cameraModel={cameraModel}
            dateFrom={dateFrom}
            dateTo={dateTo}
            dateMin={dateBounds.min}
            dateMax={dateBounds.max}
            minScore={minScore}
            maxScore={maxScore}
            facets={facets}
            cameraMakeOptions={cameraMakeOptions}
            cameraModelOptions={cameraModelOptions}
            iconScale={iconScale}
            onStatusChange={setStatus}
            onCategoryChange={setCategory}
            onCameraMakeChange={(value) => {
              setCameraMake(value);
              setCameraModel("");
            }}
            onCameraModelChange={setCameraModel}
            onDateFromChange={(value) => setDateFrom(value)}
            onDateToChange={(value) => setDateTo(value)}
            onMinScoreChange={(value) => {
              if (!Number.isFinite(value)) return;
              setMinScore(Math.min(maxScore, Math.max(0, value)));
            }}
            onMaxScoreChange={(value) => {
              if (!Number.isFinite(value)) return;
              setMaxScore(Math.max(minScore, Math.min(1, value)));
            }}
            onIconScaleChange={setIconScale}
            onReset={resetFilters}
            onToggleCollapsed={() => setFiltersCollapsed((previous) => !previous)}
            onMouseEnter={() => setFiltersHovered(true)}
            onMouseLeave={() => setFiltersHovered(false)}
          />

          <TimelineView
            itemsCount={items.length}
            total={total}
            groups={timelineGroups}
            apiBase={API_BASE}
            sort={sort}
            hasMore={hasMore}
            isLoading={isLoading}
            iconScale={iconScale}
            onSelectPhoto={setSelectedId}
            onSortChange={setSort}
            onLoadMore={() => setPage((previous) => previous + 1)}
            onJumpToBrowse={() => setViewMode("browse")}
          />

          <DetailPane
            detail={detail}
            selectedTags={selectedTags}
            apiBase={API_BASE}
            onPatchLabels={patchLabels}
            notesDraft={notesDraft}
            onNotesChange={setNotesDraft}
            onSaveNotes={saveNotes}
          />
        </div>
      )}

      {viewMode === "browse" && (
        <div className={`layout ${filtersFullyCollapsed ? "filters-collapsed" : ""}`}>
          <FiltersPane
            isCollapsed={filtersCollapsed}
            isHovered={filtersHovered}
            status={status}
            category={category}
            cameraMake={cameraMake}
            cameraModel={cameraModel}
            dateFrom={dateFrom}
            dateTo={dateTo}
            dateMin={dateBounds.min}
            dateMax={dateBounds.max}
            minScore={minScore}
            maxScore={maxScore}
            facets={facets}
            cameraMakeOptions={cameraMakeOptions}
            cameraModelOptions={cameraModelOptions}
            iconScale={iconScale}
            onStatusChange={setStatus}
            onCategoryChange={setCategory}
            onCameraMakeChange={(value) => {
              setCameraMake(value);
              setCameraModel("");
            }}
            onCameraModelChange={setCameraModel}
            onDateFromChange={(value) => setDateFrom(value)}
            onDateToChange={(value) => setDateTo(value)}
            onMinScoreChange={(value) => {
              if (!Number.isFinite(value)) return;
              setMinScore(Math.min(maxScore, Math.max(0, value)));
            }}
            onMaxScoreChange={(value) => {
              if (!Number.isFinite(value)) return;
              setMaxScore(Math.max(minScore, Math.min(1, value)));
            }}
            onIconScaleChange={setIconScale}
            onReset={resetFilters}
            onToggleCollapsed={() => setFiltersCollapsed((previous) => !previous)}
            onMouseEnter={() => setFiltersHovered(true)}
            onMouseLeave={() => setFiltersHovered(false)}
          />

          <PhotoGrid
            items={items}
            selectedId={selectedId}
            status={status}
            total={total}
            isLoading={isLoading}
            hasMore={hasMore}
            statusSummary={statusSummary}
            apiBase={API_BASE}
            sort={sort}
            iconScale={iconScale}
            loadMoreRef={loadMoreRef}
            onSelectPhoto={setSelectedId}
            onStatusChange={setStatus}
            onSortChange={setSort}
            onQuickLabel={patchLabelsForPhoto}
          />

          <DetailPane
            detail={detail}
            selectedTags={selectedTags}
            apiBase={API_BASE}
            onPatchLabels={patchLabels}
            notesDraft={notesDraft}
            onNotesChange={setNotesDraft}
            onSaveNotes={saveNotes}
          />
        </div>
      )}
    </div>
  );
}
