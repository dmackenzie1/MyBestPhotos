import type { PhotoListItem } from "@mybestphotos/shared";
import "../styles/timeline-view.css";

type TimelineGroup = {
  year: string;
  count: number;
  items: PhotoListItem[];
};

type TimelineViewProps = {
  itemsCount: number;
  groups: TimelineGroup[];
  apiBase: string;
  onSelectPhoto: (id: number) => void;
  onJumpToBrowse: () => void;
};

export function TimelineView({ itemsCount, groups, apiBase, onSelectPhoto, onJumpToBrowse }: TimelineViewProps) {
  return (
    <section className="timeline panel">
      <div className="section-header">
        <h2>Timeline</h2>
        <span>{itemsCount} photos in current filter set</span>
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
    </section>
  );
}
