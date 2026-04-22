import { useEffect, useMemo, useState } from "react";
import type { LabelPatch, PhotoDetail, PhotoListItem } from "@mybestphotos/shared";

const API_BASE = import.meta.env.VITE_API_BASE || "/api/v1";

type ViewMode = "browse" | "timeline" | "map" | "settings";

type PhotoListResponse = {
  items: PhotoListItem[];
  page: number;
  pageSize: number;
  total?: number;
  hasMore?: boolean;
};

type FacetsResponse = {
  camera: Array<{ camera_make: string | null; camera_model: string | null; count: number }>;
  categories?: Array<{ category: string; count: number }>;
};

const FALLBACK_ITEMS: PhotoListItem[] = [
  {
    id: 1,
    sourceRoot: "/photos/repo1",
    relativePath: "demo/allie-dog.jpg",
    filename: "2020_07_14_1752.jpg",
    photoTakenAt: "2020-07-14T17:52:00.000Z",
    cameraMake: "Canon",
    cameraModel: "EOS R6",
    printScore12x18: 0.92,
    printScore8x10: 0.9,
    printScore6x8: 0.94,
    curationScore: 0.93,
    descriptionText: "Young girl smiling with golden retriever in natural light.",
    keepFlag: true,
    rejectFlag: false,
    favoriteFlag: true,
  },
];

const FALLBACK_DETAIL: PhotoDetail = {
  id: 1,
  sourceRoot: "/photos/repo1",
  relativePath: "demo/allie-dog.jpg",
  filename: "2020_07_14_1752.jpg",
  extension: "jpg",
  width: 4032,
  height: 3024,
  photoTakenAt: "2020-07-14T17:52:00.000Z",
  photoTakenAtSource: "filename",
  cameraMake: "Canon",
  cameraModel: "EOS R6",
  descriptionText: "Young girl smiling with golden retriever in natural light.",
  descriptionJson: { categories: ["people", "pets"] },
  metrics: {
    blurScore: 0.12,
    brightnessScore: 0.88,
    contrastScore: 0.85,
    entropyScore: 0.81,
    noiseScore: 0.9,
    printScore6x8: 0.94,
    printScore8x10: 0.9,
    printScore12x18: 0.92,
    technicalQualityScore: 0.92,
    semanticRelevanceScore: 0.84,
    curationScore: 0.9,
  },
  labels: {
    keepFlag: true,
    rejectFlag: false,
    favoriteFlag: true,
    printCandidate6x8: true,
    printCandidate8x10: true,
    printCandidate12x18: true,
    notes: "Stub demo mode.",
  },
};

async function getJson<T>(url: string): Promise<T> {
  const response = await fetch(url);
  if (!response.ok) throw new Error(`Request failed: ${response.status}`);
  return response.json() as Promise<T>;
}

function reconcileSelection(nextItems: PhotoListItem[], previousSelected: number | null): number | null {
  if (nextItems.length === 0) return null;
  if (previousSelected && nextItems.some((item) => item.id === previousSelected)) return previousSelected;
  return nextItems[0].id;
}

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

  const pageSize = 60;

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
      } catch (_error) {
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

  return (
    <div className="shell">
      <header className="topbar">
        <div className="brand">MyBestPhotos</div>
        <input
          className="search"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search photos, scenes, and descriptions"
        />
        <nav>
          <button className={`nav-btn ${viewMode === "browse" ? "active" : ""}`} onClick={() => setViewMode("browse")}>Browse</button>
          <button className={`nav-btn ${viewMode === "timeline" ? "active" : ""}`} onClick={() => setViewMode("timeline")}>Timeline</button>
          <button className={`nav-btn ${viewMode === "map" ? "active" : ""}`} onClick={() => setViewMode("map")}>Map</button>
          <button className={`nav-btn ${viewMode === "settings" ? "active" : ""}`} onClick={() => setViewMode("settings")}>Settings</button>
        </nav>
      </header>

      {stubActive && <div className="banner">Stub mode active: API unavailable, showing sample data.</div>}

      {viewMode !== "browse" ? (
        <div className="placeholder panel">
          <h2>{viewMode === "timeline" ? "Timeline view is coming soon" : viewMode === "map" ? "Map view is coming soon" : "Settings are coming soon"}</h2>
          <p>
            {viewMode === "timeline"
              ? "Use Browse for now. Timeline filters are planned after backend date aggregations land."
              : viewMode === "map"
                ? "Use camera/date filters in Browse for now. Map support will follow GPS quality checks."
                : "Use environment variables and compose settings while we wire up in-app preferences."}
          </p>
        </div>
      ) : (
        <div className="layout">
          <aside className="filters panel">
            <h3>Filters</h3>
            <label>Status</label>
            <select value={status} onChange={(e) => setStatus(e.target.value)}>
              <option value="all">All photos</option>
              <option value="keep">Keep</option>
              <option value="favorite">Favorite</option>
              <option value="reject">Rejected</option>
              <option value="unreviewed">Unreviewed</option>
            </select>

            <label>Topic</label>
            <select value={category} onChange={(e) => setCategory(e.target.value)}>
              <option value="">Any topic</option>
              {(facets.categories || []).map((row) => (
                <option key={row.category} value={row.category}>{row.category}</option>
              ))}
            </select>

            <label>Camera Make</label>
            <select value={cameraMake} onChange={(e) => { setCameraMake(e.target.value); setCameraModel(""); }}>
              <option value="">Any camera make</option>
              {cameraMakeOptions.map((value) => (
                <option key={value} value={value}>{value}</option>
              ))}
            </select>

            <label>Camera Model</label>
            <select value={cameraModel} onChange={(e) => setCameraModel(e.target.value)}>
              <option value="">Any camera model</option>
              {cameraModelOptions.map((value) => (
                <option key={value} value={value}>{value}</option>
              ))}
            </select>

            <label>Date from</label>
            <input type="date" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} />

            <label>Date to</label>
            <input type="date" value={dateTo} onChange={(e) => setDateTo(e.target.value)} />

            <label>Min Print Score (12x18)</label>
            <input type="range" min={0.5} max={1} step={0.01} value={minScore} onChange={(e) => setMinScore(Number(e.target.value))} />
            <div className="score-val">{minScore.toFixed(2)}</div>
          </aside>

          <main className="grid-area panel">
            <div className="grid-head">
              <h2>Top photos</h2>
              <span>{items.length} loaded / {total || items.length} total</span>
            </div>

            <div className="grid">
              {items.map((item) => (
                <button key={item.id} className={`card ${selectedId === item.id ? "selected" : ""}`} onClick={() => setSelectedId(item.id)}>
                  <img src={`${API_BASE}/photos/${item.id}/image?size=thumb`} alt={item.filename} loading="lazy" />
                  <div className="overlay">{item.printScore12x18?.toFixed(2) ?? "--"}</div>
                  <div className="card-body">
                    <strong>{item.filename}</strong>
                    <small>{item.photoTakenAt ? new Date(item.photoTakenAt).toLocaleString() : "Unknown date"}</small>
                  </div>
                </button>
              ))}
            </div>
            {hasMore && (
              <button className="load-more" onClick={() => setPage((prev) => prev + 1)} disabled={isLoading}>
                {isLoading ? "Loading..." : "Load more"}
              </button>
            )}
          </main>

          <section className="detail panel">
            {detail ? (
              <>
                <img src={`${API_BASE}/photos/${detail.id}/image?size=full`} alt={detail.filename} className="preview" />
                <h3>{detail.filename}</h3>
                <p>{detail.descriptionText || "No description available."}</p>
                <div className="chip-row">
                  <span className="chip">12x18 {detail.metrics.printScore12x18?.toFixed(2) ?? "--"}</span>
                  <span className="chip">Curation {detail.metrics.curationScore?.toFixed(2) ?? "--"}</span>
                  <span className="chip">Sharpness {(1 - (detail.metrics.blurScore ?? 0)).toFixed(2)}</span>
                  <span className="chip">Contrast {detail.metrics.contrastScore?.toFixed(2) ?? "--"}</span>
                </div>

                <div className="actions">
                  <button onClick={() => patchLabels({ keepFlag: true, rejectFlag: false })}>Keep</button>
                  <button onClick={() => patchLabels({ favoriteFlag: !(detail.labels.favoriteFlag ?? false) })}>Favorite</button>
                  <button onClick={() => patchLabels({ rejectFlag: true, keepFlag: false })}>Reject</button>
                </div>

                <div className="actions">
                  <button onClick={() => patchLabels({ printCandidate6x8: true })}>6x8</button>
                  <button onClick={() => patchLabels({ printCandidate8x10: true })}>8x10</button>
                  <button onClick={() => patchLabels({ printCandidate12x18: true })}>12x18</button>
                </div>

                <textarea
                  placeholder="Notes"
                  value={detail.labels.notes || ""}
                  onChange={(e) => {
                    const notes = e.target.value;
                    setDetail({ ...detail, labels: { ...detail.labels, notes } });
                  }}
                  onBlur={() => patchLabels({ notes: detail.labels.notes || "" })}
                />
              </>
            ) : (
              <p>No photos match these filters. Clear filters or search to see results.</p>
            )}
          </section>
        </div>
      )}
    </div>
  );
}
