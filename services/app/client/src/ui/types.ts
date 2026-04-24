import type { PhotoListItem } from "@mybestphotos/shared";

export type ViewMode = "browse" | "timeline";

export type PhotoListResponse = {
  items: PhotoListItem[];
  page: number;
  pageSize: number;
  total?: number;
  hasMore?: boolean;
};

export type FacetsResponse = {
  camera: Array<{ camera_make: string | null; camera_model: string | null; count: number }>;
  categories?: Array<{ category: string; count: number }>;
  dateBounds?: { min: string | null; max: string | null };
};

export type DerivedStatus = "favorite" | "hidden" | "unreviewed";
