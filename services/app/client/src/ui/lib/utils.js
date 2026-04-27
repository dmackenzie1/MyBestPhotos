export function reconcileSelection(nextItems, previousSelected) {
    if (nextItems.length === 0)
        return null;
    if (previousSelected && nextItems.some((item) => item.id === previousSelected))
        return previousSelected;
    return nextItems[0].id;
}
export function formatMetric(value) {
    if (typeof value !== "number")
        return "--";
    return value.toFixed(2);
}
export function statusFromItem(item) {
    if (item.favoriteFlag)
        return "favorite";
    return "unreviewed";
}
export function getSelectedTags(detail) {
    const categories = detail?.descriptionJson?.categories;
    if (!Array.isArray(categories))
        return [];
    return categories.filter((tag) => typeof tag === "string");
}
