import type { ViewMode } from "../types";
import { NavLink } from "react-router-dom";
import { APP_ROUTES } from "../../routes";
import "../styles/topbar.css";

type TopBarProps = {
  viewMode: ViewMode;
  search: string;
  onSearchChange: (value: string) => void;
};

export function TopBar({ viewMode, search, onSearchChange }: TopBarProps) {
  return (
    <header className="topbar">
      <div className="brand">MyBestPhotos</div>
      <div className="search-wrap">
        <input
          className="search"
          value={search}
          onChange={(event) => onSearchChange(event.target.value)}
          placeholder="Search photos, people, places, scenes..."
          aria-label="Search photos"
        />
        <button type="button" className="search-icon-btn" aria-label="Search">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>
        </button>
      </div>
      <nav>
        <NavLink
          to={APP_ROUTES.browse}
          className={`nav-btn ${viewMode === "browse" ? "active" : ""}`}
          aria-label="Switch to browse view"
        >
          Browse
        </NavLink>
        <NavLink
          to={APP_ROUTES.timeline}
          className={`nav-btn ${viewMode === "timeline" ? "active" : ""}`}
          aria-label="Switch to timeline view"
        >
          Timeline
        </NavLink>
      </nav>
    </header>
  );
}
