import type { RefObject } from "react";
import type { LabelPatch, PhotoListItem } from "@mybestphotos/shared";
import "../styles/photo-grid.css";

type PhotoGridProps = {
  items: PhotoListItem[];
  selectedId: number | null;
  status: string;
  total: number;
  isLoading: boolean;
  hasMore: boolean;
  statusSummary: { all: number; keep: number; favorite: number; reject: number; unreviewed: number };
  apiBase: string;
  sort: string;
  loadMoreRef: RefObject<HTMLDivElement>;
  onSelectPhoto: (id: number) => void;
  onStatusChange: (status: string) => void;
  onSortChange: (value: string) => void;
  onQuickLabel: (id: number, payload: LabelPatch) => Promise<void>;
};

const SORT_OPTIONS = [
  { value: "aesthetic_desc", label: "Aesthetic" },
  { value: "curation_desc", label: "Curation" },
  { value: "print_12x18_desc", label: "Print Score" },
  { value: "date_desc", label: "Date (Newest)" },
  { value: "date_asc", label: "Date (Oldest)" },
  { value: "filename_asc", label: "Filename" },
];

export function PhotoGrid({
  items,
  selectedId,
  status,
  total,
  isLoading,
  hasMore,
  statusSummary,
  apiBase,
  sort,
  loadMoreRef,
  onSelectPhoto,
  onStatusChange,
  onSortChange,
  onQuickLabel,
}: PhotoGridProps) {
  return (
    <main className="grid-area panel">
      <div className="status-tabs">
        <button className={`status-tab ${status === "all" ? "active" : ""}`} onClick={() => onStatusChange("all")}>All <span>{statusSummary.all}</span></button>
        <button className={`status-tab ${status === "favorite" ? "active" : ""}`} onClick={() => onStatusChange("favorite")}>Favorites <span>{statusSummary.favorite}</span></button>
        <button className={`status-tab ${status === "reject" ? "active" : ""}`} onClick={() => onStatusChange("reject")}>Rejected <span>{statusSummary.reject}</span></button>
        <button className={`status-tab ${status === "keep" ? "active" : ""}`} onClick={() => onStatusChange("keep")}>For Print <span>{statusSummary.keep}</span></button>
      </div>

      <div className="grid-head">
        <h2>Browse photos</h2>
        <div className="grid-controls">
          <span>{items.length} loaded / {total || items.length} total</span>
          <label className="grid-sort">
            Sort
            <select value={sort} onChange={(event) => onSortChange(event.target.value)}>
              {SORT_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>{option.label}</option>
              ))}
            </select>
          </label>
        </div>
      </div>

      <div className="grid compact">
        {items.map((item) => (
          <article
            key={item.id}
            className={`card ${selectedId === item.id ? "selected" : ""}`}
            role="button"
            tabIndex={0}
            onClick={() => onSelectPhoto(item.id)}
            onKeyDown={(event) => {
              if (event.key === "Enter" || event.key === " ") onSelectPhoto(item.id);
            }}
          >
            <img src={`${apiBase}/photos/${item.id}/image?size=thumb`} alt={item.filename} loading="lazy" />
            <div className="overlay">
              <span>{item.aestheticScore?.toFixed(2) ?? "--"}</span>
              <span className="secondary">{item.printScore12x18?.toFixed(2) ?? "--"}</span>
            </div>
            <div className="card-actions" onClick={(event) => event.stopPropagation()}>
              <button title="Keep" onClick={() => void onQuickLabel(item.id, { keepFlag: true, rejectFlag: false })}>＋</button>
              <button title="Favorite" onClick={() => void onQuickLabel(item.id, { favoriteFlag: true })}>★</button>
              <button title="Reject" onClick={() => void onQuickLabel(item.id, { rejectFlag: true, keepFlag: false })}>－</button>
              <a title="Open full image" href={`${apiBase}/photos/${item.id}/image?size=full`} target="_blank" rel="noreferrer">⤢</a>
            </div>
            <div className="card-body">
              <strong>{item.filename}</strong>
              <small>{item.photoTakenAt ? new Date(item.photoTakenAt).toLocaleString() : "Unknown date"}</small>
            </div>
          </article>
        ))}
      </div>

      <div ref={loadMoreRef} className="infinite-sentinel" aria-hidden="true" />
      {isLoading && <div className="loading">Loading more photos…</div>}
      {!hasMore && items.length > 0 && <div className="loading done">You've reached the end of this result set.</div>}
    </main>
  );
}
