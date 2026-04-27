import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import "../styles/photo-grid.css";
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
const SORT_HELP_TEXT = {
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
function scoreBadgeForSort(item, sort) {
    if (sort === "curation_desc")
        return item.curationScore?.toFixed(2) ?? "--";
    if (sort === "aesthetic_desc")
        return item.aestheticScore?.toFixed(2) ?? "--";
    if (sort === "date_desc" || sort === "date_asc") {
        return item.photoTakenAt ? String(new Date(item.photoTakenAt).getFullYear()) : "--";
    }
    return "Rank";
}
export function PhotoGrid({ items, selectedId, status, total, isLoading, hasMore, statusSummary, apiBase, sort, iconScale, loadMoreRef, onSelectPhoto, onStatusChange, onSortChange, onQuickLabel, }) {
    return (_jsxs("main", { id: "main-content", className: "grid-area panel", children: [_jsxs("div", { className: "status-tabs", role: "tablist", "aria-label": "Photo status filters", children: [_jsxs("button", { type: "button", role: "tab", "aria-selected": status === "all", "aria-label": "Show main photos", className: `status-tab ${status === "all" ? "active" : ""}`, onClick: () => onStatusChange("all"), children: ["Main ", _jsx("span", { children: statusSummary.all })] }), _jsxs("button", { type: "button", role: "tab", "aria-selected": status === "favorite", "aria-label": "Show favorite photos", className: `status-tab ${status === "favorite" ? "active" : ""}`, onClick: () => onStatusChange("favorite"), children: ["Favorites ", _jsx("span", { children: statusSummary.favorite })] }), _jsxs("button", { type: "button", role: "tab", "aria-selected": status === "unreviewed", "aria-label": "Show unreviewed photos", className: `status-tab ${status === "unreviewed" ? "active" : ""}`, onClick: () => onStatusChange("unreviewed"), children: ["Unreviewed ", _jsx("span", { children: statusSummary.unreviewed })] })] }), _jsx("div", { className: "grid-head", children: _jsxs("div", { className: "grid-controls", children: [_jsxs("span", { children: [items.length, " loaded / ", total || items.length, " total"] }), _jsxs("label", { className: "grid-sort", children: ["Sort", _jsx("select", { value: sort, onChange: (event) => onSortChange(event.target.value), children: SORT_OPTIONS.map((option) => (_jsx("option", { value: option.value, children: option.label }, option.value))) })] })] }) }), _jsx("p", { className: "sort-help", children: SORT_HELP_TEXT[sort] ?? "Sort photos using the selected strategy." }), _jsx("div", { className: "grid compact", style: { "--icon-scale": String(iconScale) }, children: items.map((item) => (_jsxs("article", { className: `card ${selectedId === item.id ? "selected" : ""} ${item.favoriteFlag ? "favorite-frame" : ""}`, style: { "--icon-scale": String(iconScale) }, role: "button", tabIndex: 0, onClick: () => onSelectPhoto(item.id), onKeyDown: (event) => {
                        if (event.key === "Enter" || event.key === " ")
                            onSelectPhoto(item.id);
                    }, children: [_jsx("img", { src: `${apiBase}/photos/${item.id}/image?size=thumb`, alt: item.filename, loading: "lazy" }), _jsx("div", { className: "overlay", children: _jsx("span", { children: scoreBadgeForSort(item, sort) }) }), _jsxs("div", { className: "card-actions", onClick: (event) => event.stopPropagation(), children: [_jsx("button", { type: "button", "aria-label": item.favoriteFlag ? "Unfavorite photo" : "Favorite photo", title: item.favoriteFlag ? "Unfavorite" : "Favorite", onClick: () => void onQuickLabel(item.id, { favoriteFlag: !(item.favoriteFlag ?? false) }), children: "\u2605" }), _jsx("a", { "aria-label": "Open full image in new tab", title: "Open full image", href: `${apiBase}/photos/${item.id}/image?size=full&downloadName=${encodeURIComponent(item.filename)}`, target: "_blank", rel: "noreferrer", children: "\u2922" }), _jsx("a", { "aria-label": "Download original image", title: "Download original", href: `${apiBase}/photos/${item.id}/image?size=full&download=1&downloadName=${encodeURIComponent(item.filename)}`, download: item.filename, children: "\u2913" })] }), _jsxs("div", { className: "card-body", children: [_jsx("strong", { children: item.filename }), _jsx("small", { children: item.photoTakenAt ? new Date(item.photoTakenAt).toLocaleString() : "Unknown date" })] })] }, item.id))) }), _jsx("div", { ref: loadMoreRef, className: "infinite-sentinel", "aria-hidden": "true" }), isLoading && _jsx("div", { className: "loading", children: "Loading more photos\u2026" }), !hasMore && items.length > 0 && _jsx("div", { className: "loading done", children: "You've reached the end of this result set." })] }));
}
