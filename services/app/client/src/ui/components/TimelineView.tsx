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
  { value: "date_desc", label: "Date (Newest)" },
  { value: "date_asc", label: "Date (Oldest)" },
  { value: "aesthetic_desc", label: "Aesthetic" },
  { value: "curation_desc", label: "Curation" },
  { value: "print_12x18_desc", label: "Print Score" },
  { value: "filename_asc", label: "Filename" },
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
    <section className="timeline panel">
      <div className="section-header">
        <h2>Timeline</h2>
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
      <p className="sort-help">Timeline groups by year; sorting changes order inside each group.</p>
      {groups.map((group) => (
        <div key={group.year} className="timeline-group">
          <h3>{group.year} <small>{group.count} photos</small></h3>
          <div className="timeline-row">
            {group.items.map((item) => (
              <button
                key={item.id}
                className="timeline-item"
                style={{ "--icon-scale": String(iconScale) } as CSSProperties}
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
