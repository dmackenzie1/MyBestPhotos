import type { ViewMode } from "../types";
import "../styles/topbar.css";

type TopBarProps = {
  viewMode: ViewMode;
  search: string;
  onSearchChange: (value: string) => void;
  onViewModeChange: (mode: ViewMode) => void;
  sort: string;
  onSortChange: (value: string) => void;
};

const SORT_OPTIONS = [
  { value: "aesthetic_desc", label: "Aesthetic" },
  { value: "curation_desc", label: "Curation" },
  { value: "print_12x18_desc", label: "Print Score" },
  { value: "date_desc", label: "Date (Newest)" },
  { value: "date_asc", label: "Date (Oldest)" },
  { value: "filename_asc", label: "Filename" },
];

export function TopBar({ viewMode, search, onSearchChange, onViewModeChange, sort, onSortChange }: TopBarProps) {
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
      <div className="sort-select">
        <select value={sort} onChange={(event) => onSortChange(event.target.value)}>
          {SORT_OPTIONS.map((option) => (
            <option key={option.value} value={option.value}>{option.label}</option>
          ))}
        </select>
      </div>
    </header>
  );
}
