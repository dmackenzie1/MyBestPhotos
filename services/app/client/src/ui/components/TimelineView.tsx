import type { CSSProperties } from "react";
import type { PhotoListItem } from "@mybestphotos/shared";
import "../styles/timeline-view.css";

type TimelineGroup = {
  year: string;
  count: number;
  items: PhotoListItem[];
};

type TimelineViewProps = {
  itemsCount: number;
  total: number;
  groups: TimelineGroup[];
  apiBase: string;
  sort: string;
  hasMore: boolean;
  isLoading: boolean;
  iconScale: number;
  onSelectPhoto: (id: number) => void;
  onSortChange: (value: string) => void;
  onLoadMore: () => void;
  onJumpToBrowse: () => void;
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

export function TimelineView({
  itemsCount,
  total,
  groups,
  apiBase,
  sort,
  hasMore,
  isLoading,
  iconScale,
  onSelectPhoto,
  onSortChange,
  onLoadMore,
  onJumpToBrowse,
}: TimelineViewProps) {
  return (
    <section className="timeline panel" style={{ "--icon-scale": String(iconScale) } as CSSProperties}>
      <div className="section-header">
        <div className="timeline-actions">
          <span>{itemsCount} loaded / {total || itemsCount} matching</span>
          <label className="grid-sort timeline-sort">
            Sort
            <select value={sort} onChange={(event) => onSortChange(event.target.value)}>
              {SORT_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>{option.label}</option>
              ))}
            </select>
          </label>
        </div>
      </div>
      {groups.map((group) => (
        <div key={group.year} className="timeline-group">
          <h3>{group.year} <small>{group.count} photos</small></h3>
          <div className="timeline-row">
            {group.items.map((item) => (
              <button
                key={item.id}
                className="timeline-item"
                onClick={() => {
                  onSelectPhoto(item.id);
                  onJumpToBrowse();
                }}
              >
                <img src={`${apiBase}/photos/${item.id}/image?size=thumb`} alt={item.filename} loading="lazy" />
                <span>{item.filename}</span>
              </button>
            ))}
          </div>
        </div>
      ))}
      {hasMore && (
        <div className="timeline-load-more-wrap">
          <button className="timeline-load-more" onClick={onLoadMore} disabled={isLoading}>
            {isLoading ? "Loading…" : "Load more photos"}
          </button>
        </div>
      )}
    </section>
  );
}
