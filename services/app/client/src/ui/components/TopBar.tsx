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
      <input
        className="search"
        value={search}
        onChange={(event) => onSearchChange(event.target.value)}
        placeholder="Search photos, people, places, scenes..."
        aria-label="Search photos"
      />
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
