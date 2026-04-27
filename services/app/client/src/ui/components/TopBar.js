import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { NavLink } from "react-router-dom";
import { APP_ROUTES } from "../../routes";
import "../styles/topbar.css";
export function TopBar({ viewMode, search, onSearchChange }) {
    return (_jsxs("header", { className: "topbar", children: [_jsx("div", { className: "brand", children: "MyBestPhotos" }), _jsxs("div", { className: "search-wrap", children: [_jsx("input", { className: "search", value: search, onChange: (event) => onSearchChange(event.target.value), placeholder: "Search photos, people, places, scenes...", "aria-label": "Search photos" }), _jsx("button", { type: "button", className: "search-icon-btn", "aria-label": "Search", children: _jsxs("svg", { width: "16", height: "16", viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", strokeWidth: "2", strokeLinecap: "round", strokeLinejoin: "round", children: [_jsx("circle", { cx: "11", cy: "11", r: "8" }), _jsx("path", { d: "m21 21-4.3-4.3" })] }) })] }), _jsxs("nav", { children: [_jsx(NavLink, { to: APP_ROUTES.browse, className: `nav-btn ${viewMode === "browse" ? "active" : ""}`, "aria-label": "Switch to browse view", children: "Browse" }), _jsx(NavLink, { to: APP_ROUTES.timeline, className: `nav-btn ${viewMode === "timeline" ? "active" : ""}`, "aria-label": "Switch to timeline view", children: "Timeline" })] })] }));
}
