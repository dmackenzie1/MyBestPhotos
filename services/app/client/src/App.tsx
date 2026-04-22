import { useEffect, useMemo, useState } from "react";
import type { LabelPatch, PhotoDetail, PhotoListItem } from "@mybestphotos/shared";

const API_BASE = import.meta.env.VITE_API_BASE || "/api/v1";

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

export default function App() {
  const [items, setItems] = useState<PhotoListItem[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [detail, setDetail] = useState<PhotoDetail | null>(null);
  const [search, setSearch] = useState("");
  const [minScore, setMinScore] = useState(0.6);
  const [status, setStatus] = useState("all");
  const [stubActive, setStubActive] = useState(false);

  const queryString = useMemo(() => {
    const params = new URLSearchParams();
    if (search.trim()) params.set("q", search.trim());
    params.set("minPrintScore12x18", String(minScore));
    params.set("status", status);
    params.set("pageSize", "120");
    params.set("sort", "print_12x18_desc");
    return params.toString();
  }, [search, minScore, status]);

  async function refreshList() {
    try {
      const data = await getJson<{ items: PhotoListItem[] }>(`${API_BASE}/photos?${queryString}`);
      setStubActive(false);
      setItems(data.items);
      if (!selectedId && data.items.length > 0) setSelectedId(data.items[0].id);
    } catch (_error) {
      setStubActive(true);
      setItems(FALLBACK_ITEMS);
      setSelectedId(1);
    }
  }

  useEffect(() => {
    void refreshList();
  }, [queryString]);

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
    await Promise.all([refreshList(), getJson<PhotoDetail>(`${API_BASE}/photos/${selectedId}`).then(setDetail)]);
  }

  return (
    <div className="shell">
      <header className="topbar">
        <div className="brand">PhotoFlow</div>
        <input className="search" value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search photos, people, places, objects..." />
        <nav>
          <button className="nav-btn active">Browse</button>
          <button className="nav-btn">Timeline</button>
          <button className="nav-btn">Map</button>
          <button className="nav-btn">Settings</button>
        </nav>
      </header>

      {stubActive && <div className="banner">Stub mode active: API unavailable, showing sample data.</div>}

      <div className="layout">
        <aside className="filters panel">
          <h3>Filters</h3>
          <label>Status</label>
          <select value={status} onChange={(e) => setStatus(e.target.value)}>
            <option value="all">All Photos</option>
            <option value="keep">Keep</option>
            <option value="favorite">Favorite</option>
            <option value="reject">Rejected</option>
            <option value="unreviewed">Unreviewed</option>
          </select>

          <label>Min Print Score (12x18)</label>
          <input type="range" min={0.5} max={1} step={0.01} value={minScore} onChange={(e) => setMinScore(Number(e.target.value))} />
          <div className="score-val">{minScore.toFixed(2)}</div>
        </aside>

        <main className="grid-area panel">
          <div className="grid-head">
            <h2>All Photos</h2>
            <span>{items.length} shown</span>
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
        </main>

        <section className="detail panel">
          {detail ? (
            <>
              <img src={`${API_BASE}/photos/${detail.id}/image?size=full`} alt={detail.filename} className="preview" />
              <h3>{detail.filename}</h3>
              <p>{detail.descriptionText || "No description available."}</p>
              <div className="chip-row">
                <span className="chip">12x18 {detail.metrics.printScore12x18?.toFixed(2) ?? "--"}</span>
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
            <p>Select a photo.</p>
          )}
        </section>
      </div>
    </div>
  );
}
