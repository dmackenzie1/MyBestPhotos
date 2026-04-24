import type { CSSProperties, RefObject } from "react";
import type { LabelPatch, PhotoListItem } from "@mybestphotos/shared";
import "../styles/photo-grid.css";

type PhotoGridProps = {
  items: PhotoListItem[];
  selectedId: number | null;
  status: string;
  total: number;
  isLoading: boolean;
  hasMore: boolean;
  statusSummary: { all: number; favorite: number; hidden: number; unreviewed: number };
  apiBase: string;
  sort: string;
  iconScale: number;
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
];

const SORT_HELP_TEXT: Record<string, string> = {
  aesthetic_desc: "Aesthetic ranks visual appeal predicted by the model.",
  curation_desc: "Curation blends aesthetic, technical quality, and semantic context.",
  print_12x18_desc: "Print Score prioritizes sharpness/detail for 12x18 output.",
  date_desc: "Newest first by photo timestamp.",
  date_asc: "Oldest first by photo timestamp.",
  filename_asc: "Alphabetical by filename.",
};

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
  iconScale,
  loadMoreRef,
  onSelectPhoto,
  onStatusChange,
  onSortChange,
  onQuickLabel,
}: PhotoGridProps) {
  return (
    <main className="grid-area panel">
      <div className="status-tabs">
        <button type="button" className={`status-tab ${status === "all" ? "active" : ""}`} onClick={() => onStatusChange("all")}>Main <span>{statusSummary.all}</span></button>
        <button type="button" className={`status-tab ${status === "favorite" ? "active" : ""}`} onClick={() => onStatusChange("favorite")}>Favorites <span>{statusSummary.favorite}</span></button>
        <button type="button" className={`status-tab ${status === "hidden" ? "active" : ""}`} onClick={() => onStatusChange("hidden")}>Hidden <span>{statusSummary.hidden}</span></button>
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
      <p className="sort-help">{SORT_HELP_TEXT[sort] ?? "Sort photos using the selected strategy."}</p>

      <div className="grid compact">
        {items.map((item) => (
          <article
            key={item.id}
            className={`card ${selectedId === item.id ? "selected" : ""}`}
            style={{ "--icon-scale": String(iconScale) } as CSSProperties}
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
              <button
                type="button"
                title={item.favoriteFlag ? "Unfavorite" : "Favorite"}
                onClick={() => void onQuickLabel(item.id, { favoriteFlag: !(item.favoriteFlag ?? false) })}
              >
                ★
              </button>
              {item.rejectFlag ? (
                <button type="button" title="Show in main" onClick={() => void onQuickLabel(item.id, { rejectFlag: false })}>＋</button>
              ) : (
                <button type="button" title="Hide from main" onClick={() => void onQuickLabel(item.id, { rejectFlag: true, keepFlag: false })}>－</button>
              )}
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
