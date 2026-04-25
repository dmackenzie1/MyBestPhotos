import { z } from "zod";

export const listQuerySchema = z.object({
  q: z.string().optional(),
  dateFrom: z.string().optional(),
  dateTo: z.string().optional(),
  cameraMake: z.string().optional(),
  cameraModel: z.string().optional(),
  category: z.string().optional(),
  status: z.enum(["all", "favorite", "unreviewed"]).default("all"),
  page: z.coerce.number().min(1).default(1),
  pageSize: z.coerce.number().min(1).max(200).default(40),
  sort: z
    .enum([
      "date_desc",
      "date_asc",
      "curation_desc",
      "aesthetic_desc",
      "keep_desc",
      "keep_asc",
      "sharpness_desc",
      "exposure_desc",
      "contrast_desc",
      "noise_asc",
      "filename_asc",
    ])
    .default("aesthetic_desc"),
});

export const statusSummaryQuerySchema = z.object({
  q: z.string().optional(),
  dateFrom: z.string().optional(),
  dateTo: z.string().optional(),
  cameraMake: z.string().optional(),
  cameraModel: z.string().optional(),
  category: z.string().optional(),
});

export type ListQuery = z.infer<typeof listQuerySchema>;

export type SqlFilters = {
  whereSql: string;
  params: Array<string | number>;
};

type FilterQuery = Pick<
  ListQuery,
  | "q"
  | "dateFrom"
  | "dateTo"
  | "cameraMake"
  | "cameraModel"
  | "category"
  | "status"
>;

export function buildPhotoFilters(query: FilterQuery, includeStatus = true): SqlFilters {
  const where: string[] = [];
  const params: Array<string | number> = [];

  if (query.q) {
    params.push(query.q);
    where.push(
      `to_tsvector('english', coalesce(flm.description_text, fd.description_text, '')) @@ plainto_tsquery('english', $${params.length})`,
    );
  }
  if (query.dateFrom) {
    params.push(query.dateFrom);
    where.push(`f.photo_taken_at >= $${params.length}::timestamptz`);
  }
  if (query.dateTo) {
    params.push(query.dateTo);
    where.push(`f.photo_taken_at <= $${params.length}::timestamptz`);
  }
  if (query.cameraMake) {
    params.push(query.cameraMake);
    where.push(`f.camera_make = $${params.length}`);
  }
  if (query.cameraModel) {
    params.push(query.cameraModel);
    where.push(`f.camera_model = $${params.length}`);
  }
  if (query.category) {
    params.push(query.category);
    where.push(
      `(EXISTS (
        SELECT 1
        FROM jsonb_array_elements_text(coalesce(fd.description_json->'categories', '[]'::jsonb)) AS c(category)
        WHERE c.category = $${params.length}
      ) OR $${params.length} = ANY(coalesce(flm.tags, ARRAY[]::text[])))`,
    );
  }
  if (includeStatus) {
    if (query.status === "all") where.push("TRUE");
    if (query.status === "favorite") where.push("fl.favorite_flag = true");
    if (query.status === "unreviewed") where.push("fl.file_id is null");
  }

  return {
    whereSql: where.length ? `WHERE ${where.join(" AND ")}` : "",
    params,
  };
}

const ORDER_BY_SQL: Record<ListQuery["sort"], string> = {
  date_asc: "f.photo_taken_at ASC NULLS LAST",
  date_desc: "f.photo_taken_at DESC NULLS LAST",
  curation_desc: "fm.curation_score DESC NULLS LAST",
  aesthetic_desc: "fm.aesthetic_score DESC NULLS LAST",
  keep_desc: "fm.keep_score DESC NULLS LAST",
  keep_asc: "fm.keep_score ASC NULLS FIRST",
  sharpness_desc: "fm.blur_score ASC NULLS LAST",
  exposure_desc: "fm.brightness_score DESC NULLS LAST",
  contrast_desc: "fm.contrast_score DESC NULLS LAST",
  noise_asc: "fm.noise_score ASC NULLS LAST",
  filename_asc: "f.filename ASC",
};

export function getOrderBySql(sort: ListQuery["sort"]): string {
  return ORDER_BY_SQL[sort] ?? ORDER_BY_SQL.date_desc;
}
