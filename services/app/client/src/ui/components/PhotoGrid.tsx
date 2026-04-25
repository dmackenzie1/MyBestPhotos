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
  statusSummary: { all: number; favorite: number; unreviewed: number };
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
  { value: "curation_desc", label: "Curation" },
  { value: "aesthetic_desc", label: "Aesthetic" },
  { value: "sharpness_desc", label: "Sharpness" },
  { value: "exposure_desc", label: "Exposure" },
  { value: "contrast_desc", label: "Contrast" },
  { value: "noise_asc", label: "Noise (Low to High)" },
  { value: "random", label: "Random" },
  { value: "date_desc", label: "Date (Newest)" },
  { value: "date_asc", label: "Date (Oldest)" },
];

const SORT_HELP_TEXT: Record<string, string> = {
  aesthetic_desc: "Aesthetic ranks visual appeal predicted by the model.",
  curation_desc: "Curation blends aesthetic, technical quality, and semantic context.",
  sharpness_desc: "Sharpness ranks photos with less blur first.",
  exposure_desc: "Exposure ranks brighter exposures first.",
  contrast_desc: "Contrast ranks punchier contrast first.",
  noise_asc: "Noise ranks cleaner photos (lower noise) first.",
  random: "Random shuffles results each load for variety.",
  date_desc: "Newest first by photo timestamp.",
  date_asc: "Oldest first by photo timestamp.",
};

function scoreBadgeForSort(item: PhotoListItem, sort: string): string {
  if (sort === "curation_desc") return item.curationScore?.toFixed(2) ?? "--";
  if (sort === "aesthetic_desc") return item.aestheticScore?.toFixed(2) ?? "--";
  if (sort === "date_desc" || sort === "date_asc") {
    return item.photoTakenAt ? String(new Date(item.photoTakenAt).getFullYear()) : "--";
  }
  return "Rank";
}

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
    <main id="main-content" className="grid-area panel">
      <div className="status-tabs" role="tablist" aria-label="Photo status filters">
        <button type="button" role="tab" aria-selected={status === "all"} aria-label="Show main photos" className={`status-tab ${status === "all" ? "active" : ""}`} onClick={() => onStatusChange("all")}>Main <span>{statusSummary.all}</span></button>
        <button type="button" role="tab" aria-selected={status === "favorite"} aria-label="Show favorite photos" className={`status-tab ${status === "favorite" ? "active" : ""}`} onClick={() => onStatusChange("favorite")}>Favorites <span>{statusSummary.favorite}</span></button>
        <button type="button" role="tab" aria-selected={status === "unreviewed"} aria-label="Show unreviewed photos" className={`status-tab ${status === "unreviewed" ? "active" : ""}`} onClick={() => onStatusChange("unreviewed")}>Unreviewed <span>{statusSummary.unreviewed}</span></button>
      </div>

      <div className="grid-head">
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

      <div className="grid compact" style={{ "--icon-scale": String(iconScale) } as CSSProperties}>
        {items.map((item) => (
          <article
            key={item.id}
            className={`card ${selectedId === item.id ? "selected" : ""} ${item.favoriteFlag ? "favorite-frame" : ""}`}
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
              <span>{scoreBadgeForSort(item, sort)}</span>
            </div>
            <div className="card-actions" onClick={(event) => event.stopPropagation()}>
              <button
                type="button"
                aria-label={item.favoriteFlag ? "Unfavorite photo" : "Favorite photo"}
                title={item.favoriteFlag ? "Unfavorite" : "Favorite"}
                onClick={() => void onQuickLabel(item.id, { favoriteFlag: !(item.favoriteFlag ?? false) })}
              >
                ★
              </button>
              <a
                aria-label="Open full image in new tab"
                title="Open full image"
                href={`${apiBase}/photos/${item.id}/image?size=full&downloadName=${encodeURIComponent(item.filename)}`}
                target="_blank"
                rel="noreferrer"
              >
                ⤢
              </a>
              <a
                aria-label="Download original image"
                title="Download original"
                href={`${apiBase}/photos/${item.id}/image?size=full&download=1&downloadName=${encodeURIComponent(item.filename)}`}
                download={item.filename}
              >
                ⤓
              </a>
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
