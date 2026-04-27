import { jsxs as _jsxs, jsx as _jsx } from "react/jsx-runtime";
import "../styles/timeline-view.css";
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
export function TimelineView({ itemsCount, total, groups, apiBase, sort, hasMore, isLoading, iconScale, onSelectPhoto, onSortChange, onLoadMore, onJumpToBrowse, }) {
    return (_jsxs("section", { className: "timeline panel", style: { "--icon-scale": String(iconScale) }, children: [_jsx("div", { className: "section-header", children: _jsxs("div", { className: "timeline-actions", children: [_jsxs("span", { children: [itemsCount, " loaded / ", total || itemsCount, " matching"] }), _jsxs("label", { className: "grid-sort timeline-sort", children: ["Sort", _jsx("select", { value: sort, onChange: (event) => onSortChange(event.target.value), children: SORT_OPTIONS.map((option) => (_jsx("option", { value: option.value, children: option.label }, option.value))) })] })] }) }), groups.map((group) => (_jsxs("div", { className: "timeline-group", children: [_jsxs("h3", { children: [group.year, " ", _jsxs("small", { children: [group.count, " photos"] })] }), _jsx("div", { className: "timeline-row", children: group.items.map((item) => (_jsxs("button", { className: "timeline-item", onClick: () => {
                                onSelectPhoto(item.id);
                                onJumpToBrowse();
                            }, children: [_jsx("img", { src: `${apiBase}/photos/${item.id}/image?size=thumb`, alt: item.filename, loading: "lazy" }), _jsx("span", { children: item.filename })] }, item.id))) })] }, group.year))), hasMore && (_jsx("div", { className: "timeline-load-more-wrap", children: _jsx("button", { className: "timeline-load-more", onClick: onLoadMore, disabled: isLoading, children: isLoading ? "Loading…" : "Load more photos" }) }))] }));
}
