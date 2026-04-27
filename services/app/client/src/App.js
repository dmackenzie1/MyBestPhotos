import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useEffect, useMemo, useRef, useState } from "react";
import { DetailPane } from "./ui/components/DetailPane";
import { FiltersPane } from "./ui/components/FiltersPane";
import { PhotoGrid } from "./ui/components/PhotoGrid";
import { TimelineView } from "./ui/components/TimelineView";
import { TopBar } from "./ui/components/TopBar";
import { APP_ROUTE_CONFIG, APP_ROUTES } from "./routes";
import { getJson } from "./ui/lib/api";
import { FALLBACK_DETAIL, FALLBACK_ITEMS } from "./ui/lib/fallbackData";
import { getSelectedTags, reconcileSelection } from "./ui/lib/utils";
import { useLocation, useNavigate } from "react-router-dom";
const API_BASE = import.meta.env.VITE_API_BASE || ((typeof window !== "undefined" && window.location.port === "5173")
    ? "http://localhost:3001/api/v1"
    : "/api/v1");
export default function App() {
    const location = useLocation();
    const navigate = useNavigate();
    const viewMode = location.pathname === APP_ROUTES.timeline ? "timeline" : "browse";
    useEffect(() => {
        const isKnownRoute = APP_ROUTE_CONFIG.some((route) => route.path === location.pathname);
        if (!isKnownRoute) {
            navigate(APP_ROUTES.browse, { replace: true });
        }
    }, [location.pathname, navigate]);
    const [items, setItems] = useState([]);
    const [selectedId, setSelectedId] = useState(null);
    const [detail, setDetail] = useState(null);
    const [search, setSearch] = useState("");
    const [status, setStatus] = useState("all");
    const [cameraMake, setCameraMake] = useState("");
    const [cameraModel, setCameraModel] = useState("");
    const [category, setCategory] = useState("");
    const [dateFrom, setDateFrom] = useState("");
    const [dateTo, setDateTo] = useState("");
    const [dateBounds, setDateBounds] = useState({ min: "", max: "" });
    const [notesDraft, setNotesDraft] = useState("");
    const [page, setPage] = useState(1);
    const [total, setTotal] = useState(0);
    const [hasMore, setHasMore] = useState(false);
    const [isLoading, setIsLoading] = useState(false);
    const [statusSummary, setStatusSummary] = useState({
        all: 0,
        favorite: 0,
        unreviewed: 0,
    });
    const [facets, setFacets] = useState({ camera: [], categories: [], dateBounds: { min: null, max: null } });
    const [stubActive, setStubActive] = useState(false);
    const [filtersCollapsed, setFiltersCollapsed] = useState(false);
    const [filtersHovered, setFiltersHovered] = useState(false);
    const [sort, setSort] = useState("aesthetic_desc");
    const [iconScale, setIconScale] = useState(1);
    const pageSize = 60;
    const loadMoreRef = useRef(null);
    const queryString = useMemo(() => {
        const params = new URLSearchParams();
        if (search.trim())
            params.set("q", search.trim());
        if (cameraMake)
            params.set("cameraMake", cameraMake);
        if (cameraModel)
            params.set("cameraModel", cameraModel);
        if (category)
            params.set("category", category);
        if (dateFrom)
            params.set("dateFrom", `${dateFrom}T00:00:00.000Z`);
        if (dateTo)
            params.set("dateTo", `${dateTo}T23:59:59.999Z`);
        params.set("status", status);
        params.set("page", String(page));
        params.set("pageSize", String(pageSize));
        params.set("sort", sort);
        return params.toString();
    }, [search, cameraMake, cameraModel, category, dateFrom, dateTo, status, page, sort]);
    const summaryQueryString = useMemo(() => {
        const params = new URLSearchParams();
        if (search.trim())
            params.set("q", search.trim());
        if (cameraMake)
            params.set("cameraMake", cameraMake);
        if (cameraModel)
            params.set("cameraModel", cameraModel);
        if (category)
            params.set("category", category);
        if (dateFrom)
            params.set("dateFrom", `${dateFrom}T00:00:00.000Z`);
        if (dateTo)
            params.set("dateTo", `${dateTo}T23:59:59.999Z`);
        return params.toString();
    }, [search, cameraMake, cameraModel, category, dateFrom, dateTo]);
    useEffect(() => {
        setPage(1);
    }, [search, cameraMake, cameraModel, category, dateFrom, dateTo, status, sort]);
    useEffect(() => {
        if (stubActive)
            return;
        void getJson(`${API_BASE}/facets`)
            .then((response) => {
            setFacets(response);
            const nextMin = response.dateBounds?.min ?? "";
            const nextMax = response.dateBounds?.max ?? "";
            setDateBounds({ min: nextMin, max: nextMax });
            setDateFrom((previous) => previous || nextMin);
            setDateTo((previous) => previous || nextMax);
        })
            .catch(() => setFacets({ camera: [], categories: [], dateBounds: { min: null, max: null } }));
    }, [stubActive]);
    useEffect(() => {
        let cancelled = false;
        async function loadList() {
            setIsLoading(true);
            try {
                const data = await getJson(`${API_BASE}/photos?${queryString}`);
                if (cancelled)
                    return;
                setStubActive(false);
                setItems((previousItems) => {
                    const mergedItems = page === 1 ? data.items : [...previousItems, ...data.items];
                    setSelectedId((previousSelected) => reconcileSelection(mergedItems, previousSelected));
                    return mergedItems;
                });
                setTotal(data.total ?? data.items.length);
                setHasMore(Boolean(data.hasMore));
            }
            catch {
                if (cancelled)
                    return;
                setStubActive(true);
                setItems(FALLBACK_ITEMS);
                setSelectedId(1);
                setTotal(FALLBACK_ITEMS.length);
                setHasMore(false);
            }
            finally {
                if (!cancelled)
                    setIsLoading(false);
            }
        }
        void loadList();
        return () => {
            cancelled = true;
        };
    }, [queryString, page]);
    useEffect(() => {
        if (!selectedId) {
            setDetail(null);
            setNotesDraft("");
            return;
        }
        if (stubActive) {
            setDetail(FALLBACK_DETAIL);
            setNotesDraft(FALLBACK_DETAIL.labels.notes || "");
            return;
        }
        void getJson(`${API_BASE}/photos/${selectedId}`)
            .then((photoDetail) => {
            setDetail(photoDetail);
            setNotesDraft(photoDetail.labels.notes || "");
        })
            .catch(() => {
            setStubActive(true);
            setDetail(FALLBACK_DETAIL);
            setNotesDraft(FALLBACK_DETAIL.labels.notes || "");
        });
    }, [selectedId, stubActive]);
    useEffect(() => {
        const sentinel = loadMoreRef.current;
        if (!sentinel || !hasMore)
            return;
        const observer = new IntersectionObserver((entries) => {
            const [entry] = entries;
            if (entry?.isIntersecting && !isLoading)
                setPage((previous) => previous + 1);
        }, { rootMargin: "300px 0px" });
        observer.observe(sentinel);
        return () => observer.disconnect();
    }, [hasMore, isLoading]);
    async function patchLabelsForPhoto(photoId, payload) {
        if (stubActive && detail && selectedId === photoId) {
            setDetail({ ...detail, labels: { ...detail.labels, ...payload } });
            return;
        }
        await fetch(`${API_BASE}/photos/${photoId}/labels`, {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
        });
        setItems((previousItems) => {
            const patchedItems = previousItems
                .map((item) => (item.id === photoId
                ? {
                    ...item,
                    favoriteFlag: payload.favoriteFlag === undefined ? item.favoriteFlag : payload.favoriteFlag,
                }
                : item))
                .filter((item) => {
                if (status === "all")
                    return true;
                if (status === "favorite")
                    return item.favoriteFlag === true;
                if (status === "unreviewed")
                    return item.favoriteFlag !== true;
                return true;
            });
            setSelectedId((previousSelected) => reconcileSelection(patchedItems, previousSelected));
            return patchedItems;
        });
        setDetail((previousDetail) => {
            if (!previousDetail || previousDetail.id !== photoId)
                return previousDetail;
            return {
                ...previousDetail,
                labels: {
                    ...previousDetail.labels,
                    ...payload,
                },
            };
        });
        if (!stubActive) {
            void getJson(`${API_BASE}/photos/status-summary?${summaryQueryString}`)
                .then((response) => setStatusSummary(response))
                .catch(() => undefined);
        }
    }
    async function patchLabels(payload) {
        if (!selectedId)
            return;
        await patchLabelsForPhoto(selectedId, payload);
    }
    async function saveNotes() {
        if (!detail)
            return;
        await patchLabels({ notes: notesDraft });
    }
    const cameraMakeOptions = Array.from(new Set(facets.camera.map((row) => row.camera_make).filter((row) => Boolean(row))));
    const cameraModelOptions = Array.from(new Set(facets.camera
        .filter((row) => (cameraMake ? row.camera_make === cameraMake : true))
        .map((row) => row.camera_model)
        .filter((row) => Boolean(row))));
    useEffect(() => {
        if (stubActive) {
            const fallbackSummary = {
                all: FALLBACK_ITEMS.length,
                favorite: FALLBACK_ITEMS.filter((item) => item.favoriteFlag === true).length,
                unreviewed: FALLBACK_ITEMS.filter((item) => !item.favoriteFlag).length,
            };
            setStatusSummary(fallbackSummary);
            return;
        }
        void getJson(`${API_BASE}/photos/status-summary?${summaryQueryString}`)
            .then((response) => setStatusSummary(response))
            .catch(() => {
            const fallbackSummary = { all: 0, favorite: 0, unreviewed: 0 };
            setStatusSummary(fallbackSummary);
        });
    }, [summaryQueryString, stubActive]);
    const timelineGroups = useMemo(() => {
        const grouped = new Map();
        for (const item of items) {
            const date = item.photoTakenAt ? new Date(item.photoTakenAt) : null;
            const year = date ? String(date.getFullYear()) : "Unknown";
            const bucket = grouped.get(year) || [];
            bucket.push(item);
            grouped.set(year, bucket);
        }
        return [...grouped.entries()]
            .sort((a, b) => Number(b[0]) - Number(a[0]))
            .map(([year, yearItems]) => ({ year, count: yearItems.length, items: yearItems.slice(0, 5) }));
    }, [items]);
    const selectedTags = useMemo(() => getSelectedTags(detail), [detail]);
    const filtersFullyCollapsed = filtersCollapsed && !filtersHovered;
    function resetFilters() {
        setStatus("all");
        setCategory("");
        setCameraMake("");
        setCameraModel("");
        setDateFrom(dateBounds.min);
        setDateTo(dateBounds.max);
    }
    return (_jsxs("div", { className: "shell", children: [_jsx("a", { className: "skip-link", href: "#main-content", children: "Skip to content" }), _jsx(TopBar, { viewMode: viewMode, search: search, onSearchChange: setSearch }), stubActive && _jsx("div", { className: "banner", children: "Stub mode active: API unavailable, showing sample data." }), viewMode === "timeline" && (_jsxs("div", { className: `layout timeline-layout ${filtersFullyCollapsed ? "filters-collapsed" : ""}`, children: [_jsx(FiltersPane, { isCollapsed: filtersCollapsed, isHovered: filtersHovered, status: status, category: category, cameraMake: cameraMake, cameraModel: cameraModel, dateFrom: dateFrom, dateTo: dateTo, dateMin: dateBounds.min, dateMax: dateBounds.max, facets: facets, cameraMakeOptions: cameraMakeOptions, cameraModelOptions: cameraModelOptions, iconScale: iconScale, onStatusChange: setStatus, onCategoryChange: setCategory, onCameraMakeChange: (value) => {
                            setCameraMake(value);
                            setCameraModel("");
                        }, onCameraModelChange: setCameraModel, onDateFromChange: (value) => setDateFrom(value), onDateToChange: (value) => setDateTo(value), onIconScaleChange: setIconScale, onReset: resetFilters, onToggleCollapsed: () => setFiltersCollapsed((previous) => !previous), onMouseEnter: () => setFiltersHovered(true), onMouseLeave: () => setFiltersHovered(false) }), _jsx(TimelineView, { itemsCount: items.length, total: total, groups: timelineGroups, apiBase: API_BASE, sort: sort, hasMore: hasMore, isLoading: isLoading, iconScale: iconScale, onSelectPhoto: setSelectedId, onSortChange: setSort, onLoadMore: () => setPage((previous) => previous + 1), onJumpToBrowse: () => navigate(APP_ROUTES.browse) }), _jsx(DetailPane, { detail: detail, selectedTags: selectedTags, apiBase: API_BASE, onPatchLabels: patchLabels, notesDraft: notesDraft, onNotesChange: setNotesDraft, onSaveNotes: saveNotes })] })), viewMode === "browse" && (_jsxs("div", { className: `layout ${filtersFullyCollapsed ? "filters-collapsed" : ""}`, children: [_jsx(FiltersPane, { isCollapsed: filtersCollapsed, isHovered: filtersHovered, status: status, category: category, cameraMake: cameraMake, cameraModel: cameraModel, dateFrom: dateFrom, dateTo: dateTo, dateMin: dateBounds.min, dateMax: dateBounds.max, facets: facets, cameraMakeOptions: cameraMakeOptions, cameraModelOptions: cameraModelOptions, iconScale: iconScale, onStatusChange: setStatus, onCategoryChange: setCategory, onCameraMakeChange: (value) => {
                            setCameraMake(value);
                            setCameraModel("");
                        }, onCameraModelChange: setCameraModel, onDateFromChange: (value) => setDateFrom(value), onDateToChange: (value) => setDateTo(value), onIconScaleChange: setIconScale, onReset: resetFilters, onToggleCollapsed: () => setFiltersCollapsed((previous) => !previous), onMouseEnter: () => setFiltersHovered(true), onMouseLeave: () => setFiltersHovered(false) }), _jsx(PhotoGrid, { items: items, selectedId: selectedId, status: status, total: total, isLoading: isLoading, hasMore: hasMore, statusSummary: statusSummary, apiBase: API_BASE, sort: sort, iconScale: iconScale, loadMoreRef: loadMoreRef, onSelectPhoto: setSelectedId, onStatusChange: setStatus, onSortChange: setSort, onQuickLabel: patchLabelsForPhoto }), _jsx(DetailPane, { detail: detail, selectedTags: selectedTags, apiBase: API_BASE, onPatchLabels: patchLabels, notesDraft: notesDraft, onNotesChange: setNotesDraft, onSaveNotes: saveNotes })] }))] }));
}
