import type { RefObject } from "react";
import type { PhotoListItem } from "@mybestphotos/shared";
import type { SettingsState } from "../types";
import "../styles/photo-grid.css";

type PhotoGridProps = {
  items: PhotoListItem[];
  selectedId: number | null;
  status: string;
  total: number;
  isLoading: boolean;
  hasMore: boolean;
  settings: SettingsState;
  statusSummary: { all: number; keep: number; favorite: number; reject: number; unreviewed: number };
  apiBase: string;
  loadMoreRef: RefObject<HTMLDivElement>;
  onSelectPhoto: (id: number) => void;
  onStatusChange: (status: string) => void;
};

export function PhotoGrid({
  items,
  selectedId,
  status,
  total,
  isLoading,
  hasMore,
  settings,
  statusSummary,
  apiBase,
  loadMoreRef,
  onSelectPhoto,
  onStatusChange,
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
        <span>{items.length} loaded / {total || items.length} total</span>
      </div>

      <div className={`grid ${settings.compactCards || settings.density === "compact" ? "compact" : ""}`}>
        {items.map((item) => (
          <button key={item.id} className={`card ${selectedId === item.id ? "selected" : ""}`} onClick={() => onSelectPhoto(item.id)}>
            <img src={`${apiBase}/photos/${item.id}/image?size=thumb`} alt={item.filename} loading="lazy" />
            {settings.showScores && (
              <div className="overlay">
                <span>{item.aestheticScore?.toFixed(2) ?? "--"}</span>
                <span className="secondary">{item.printScore12x18?.toFixed(2) ?? "--"}</span>
              </div>
            )}
            <div className="card-body">
              <strong>{item.filename}</strong>
              <small>{item.photoTakenAt ? new Date(item.photoTakenAt).toLocaleString() : "Unknown date"}</small>
            </div>
          </button>
        ))}
      </div>

      <div ref={loadMoreRef} className="infinite-sentinel" aria-hidden="true" />
      {isLoading && <div className="loading">Loading more photos…</div>}
      {!hasMore && items.length > 0 && <div className="loading done">You've reached the end of this result set.</div>}
    </main>
  );
}
