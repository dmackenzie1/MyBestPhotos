import type { PhotoDetail, PhotoListItem } from "@mybestphotos/shared";
import type { DerivedStatus } from "../types";

export function reconcileSelection(nextItems: PhotoListItem[], previousSelected: number | null): number | null {
  if (nextItems.length === 0) return null;
  if (previousSelected && nextItems.some((item) => item.id === previousSelected)) return previousSelected;
  return nextItems[0].id;
}

export function formatMetric(value: number | null | undefined): string {
  if (typeof value !== "number") return "--";
  return value.toFixed(2);
}

export function statusFromItem(item: PhotoListItem): DerivedStatus {
  if (item.favoriteFlag) return "favorite";
  return "unreviewed";
}

export function getSelectedTags(detail: PhotoDetail | null): string[] {
  const categories = detail?.descriptionJson?.categories;
  if (!Array.isArray(categories)) return [];
  return categories.filter((tag): tag is string => typeof tag === "string");
}
