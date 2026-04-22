import type { ViewMode } from "../types";
import "../styles/topbar.css";

type TopBarProps = {
  viewMode: ViewMode;
  search: string;
  onSearchChange: (value: string) => void;
  onViewModeChange: (mode: ViewMode) => void;
};

export function TopBar({ viewMode, search, onSearchChange, onViewModeChange }: TopBarProps) {
  return (
    <header className="topbar">
      <div className="brand">MyBestPhotos</div>
      <input
        className="search"
        value={search}
        onChange={(event) => onSearchChange(event.target.value)}
        placeholder="Search photos, people, places, scenes..."
      />
      <nav>
        <button className={`nav-btn ${viewMode === "browse" ? "active" : ""}`} onClick={() => onViewModeChange("browse")}>Browse</button>
        <button className={`nav-btn ${viewMode === "timeline" ? "active" : ""}`} onClick={() => onViewModeChange("timeline")}>Timeline</button>
        <button className={`nav-btn ${viewMode === "map" ? "active" : ""}`} onClick={() => onViewModeChange("map")}>Map</button>
        <button className={`nav-btn ${viewMode === "settings" ? "active" : ""}`} onClick={() => onViewModeChange("settings")}>Settings</button>
      </nav>
    </header>
  );
}
