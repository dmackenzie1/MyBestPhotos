import cors from "cors";
import express from "express";
import path from "node:path";
import fs from "node:fs";
import { z } from "zod";
import type { LabelPatch, PhotoDetail, PhotoListItem } from "@mybestphotos/shared";
import pool, { checkHealth } from "./db.js";
import {
  buildPhotoFilters,
  getOrderBySql,
  listQuerySchema,
  statusSummaryQuerySchema,
} from "./photoQuery.js";
import { embedText, vectorLiteral } from "./textVectorizer.js";

const app = express();
app.use(cors());
app.use(express.json());

const STUB_MODE = process.env.STUB_MODE === "true";

const mockList: PhotoListItem[] = [
  {
    id: 1,
    sourceRoot: "/photos/repo1",
    relativePath: "demo/allie-dog.jpg",
    filename: "allie-dog.jpg",
    photoTakenAt: "2020-07-14T17:52:00.000Z",
    cameraMake: "Canon",
    cameraModel: "EOS R6",
    printScore12x18: 0.92,
    printScore8x10: 0.94,
    printScore6x8: 0.96,
    curationScore: 0.93,
    aestheticScore: 0.87,
    wallArtScore: 88,
    descriptionText: "Young girl smiling and hugging a golden retriever outdoors.",
    keepFlag: true,
    rejectFlag: false,
    favoriteFlag: true,
  },
  {
    id: 2,
    sourceRoot: "/photos/repo1",
    relativePath: "demo/family-yard.jpg",
    filename: "family-yard.jpg",
    photoTakenAt: "2019-09-21T10:45:00.000Z",
    cameraMake: "Canon",
    cameraModel: "EOS R6",
    printScore12x18: 0.86,
    printScore8x10: 0.88,
    printScore6x8: 0.9,
    curationScore: 0.87,
    aestheticScore: 0.82,
    wallArtScore: 79,
    descriptionText: "Family portrait in warm evening light in a backyard.",
    keepFlag: null,
    rejectFlag: null,
    favoriteFlag: null,
  },
];

const mockDetail = (id: number): PhotoDetail => {
  const selected = mockList.find((item) => item.id === id) ?? mockList[0];
  return {
    id: selected.id,
    sourceRoot: selected.sourceRoot,
    relativePath: selected.relativePath,
    filename: selected.filename,
    extension: "jpg",
    width: 4032,
    height: 3024,
    photoTakenAt: selected.photoTakenAt,
    photoTakenAtSource: "filename",
    cameraMake: selected.cameraMake,
    cameraModel: selected.cameraModel,
    descriptionText: selected.descriptionText,
    descriptionJson: {
      categories: ["people", "pets", "portrait"],
      quality_hint: "excellent",
    },
    metrics: {
      blurScore: 0.12,
      brightnessScore: 0.88,
      contrastScore: 0.84,
      entropyScore: 0.82,
      noiseScore: 0.89,
      technicalQualityScore: 0.92,
      semanticRelevanceScore: 0.85,
      curationScore: selected.curationScore,
      aestheticScore: selected.aestheticScore,
      wallArtScore: selected.wallArtScore,
      printScore6x8: selected.printScore6x8,
      printScore8x10: selected.printScore8x10,
      printScore12x18: selected.printScore12x18,
    },
    labels: {
      keepFlag: selected.keepFlag,
      rejectFlag: selected.rejectFlag,
      favoriteFlag: selected.favoriteFlag,
      printCandidate6x8: true,
      printCandidate8x10: true,
      printCandidate12x18: true,
      notes: "Stub mode: add real note support after DB run.",
    },
  };
};

const labelPatchSchema = z.object({
  keepFlag: z.boolean().nullable().optional(),
  rejectFlag: z.boolean().nullable().optional(),
  favoriteFlag: z.boolean().nullable().optional(),
  printCandidate6x8: z.boolean().nullable().optional(),
  printCandidate8x10: z.boolean().nullable().optional(),
  printCandidate12x18: z.boolean().nullable().optional(),
  notes: z.string().nullable().optional(),
});

type PhotoListRow = {
  id: number;
  source_root: string;
  relative_path: string;
  filename: string;
  photo_taken_at: string | Date | null;
  camera_make: string | null;
  camera_model: string | null;
  print_score_12x18: number | null;
  print_score_8x10: number | null;
  print_score_6x8: number | null;
  curation_score: number | null;
  aesthetic_score: number | null;
  description_text: string | null;
  wall_art_score: number | null;
  keep_flag: boolean | null;
  reject_flag: boolean | null;
  favorite_flag: boolean | null;
};

function resolveFilePath(sourceRoot: string, relativePath: string): string {
  const root = path.resolve(sourceRoot);
  const full = path.resolve(root, relativePath);
  const inRoot = full === root || full.startsWith(`${root}${path.sep}`);
  if (!inRoot) {
    throw new Error("Unsafe file path");
  }
  return full;
}

app.get("/api/v1/health", async (_req, res) => {
  const dbResult = await checkHealth();

  let pipelineInfo: Record<string, unknown> | null = null;
  try {
    const runRows = await pool.query(
      `SELECT id, run_id, started_at, completed_at, status, nima_model_version,
              total_files_ingested, total_metrics_scored, total_nima_scored, notes
       FROM pipeline_runs ORDER BY id DESC LIMIT 1`
    );
    if (runRows.rows.length > 0) {
      const r = runRows.rows[0];
      pipelineInfo = {
        last_run_id: r.run_id,
        started_at: r.started_at?.toString(),
        completed_at: r.completed_at?.toString(),
        status: r.status,
        nima_model_version: r.nima_model_version,
        total_files_ingested: Number(r.total_files_ingested),
        total_metrics_scored: Number(r.total_metrics_scored),
        total_nima_scored: Number(r.total_nima_scored),
        notes: r.notes,
      };
    }
  } catch {
    // Pipeline info unavailable; leave as null
  }

  let fileStats: Record<string, unknown> | null = null;
  try {
    const countRows = await pool.query(
      `SELECT COUNT(*)::int AS total_files,
              (SELECT COUNT(*) FROM file_metrics WHERE nima_score IS NOT NULL)::int AS scored_nima,
              (SELECT COUNT(*) FROM file_descriptions)::int AS described,
              (SELECT COUNT(*) FROM file_llm_results)::int AS llm_described
       FROM files`
    );
    if (countRows.rows.length > 0) {
      const s = countRows.rows[0];
      fileStats = {
        total_files: Number(s.total_files),
        scored_nima: Number(s.scored_nima),
        described: Number(s.described),
        llm_described: Number(s.llm_described),
      };
    }
  } catch {
    // File stats unavailable; leave as null
  }

  res.json({
    ok: dbResult.ok,
    stubMode: STUB_MODE,
    database: dbResult.ok ? "connected" : `error: ${dbResult.error}`,
    pipeline: pipelineInfo,
    fileStats,
  });
});


app.get("/api/v1/photos/status-summary", async (req, res) => {
  if (STUB_MODE) {
    res.json({
      all: mockList.filter((item) => item.rejectFlag !== true).length,
      favorite: mockList.filter((item) => item.favoriteFlag === true && item.rejectFlag !== true).length,
      hidden: mockList.filter((item) => item.rejectFlag === true).length,
      unreviewed: mockList.filter((item) => !item.keepFlag && !item.favoriteFlag && !item.rejectFlag).length,
    });
    return;
  }

  const parsed = statusSummaryQuerySchema.safeParse(req.query);
  if (!parsed.success) {
    res.status(400).json({ error: parsed.error.flatten() });
    return;
  }

  const { whereSql, params } = buildPhotoFilters({ ...parsed.data, status: "all" }, false);
  const summarySql = `
    SELECT
      COUNT(*) FILTER (WHERE coalesce(fl.reject_flag, false) = false)::int AS all_count,
      COUNT(*) FILTER (WHERE fl.favorite_flag = true AND coalesce(fl.reject_flag, false) = false)::int AS favorite_count,
      COUNT(*) FILTER (WHERE fl.reject_flag = true)::int AS hidden_count,
      COUNT(*) FILTER (WHERE fl.file_id IS NULL)::int AS unreviewed_count
    FROM files f
    LEFT JOIN file_metrics fm ON fm.file_id = f.id
    LEFT JOIN file_descriptions fd ON fd.file_id = f.id
    LEFT JOIN file_labels fl ON fl.file_id = f.id
    LEFT JOIN file_llm_results flm ON flm.file_id = f.id
    ${whereSql}
  `;

  const result = await pool.query(summarySql, params);
  const row = result.rows[0] ?? {};
  res.json({
    all: Number(row.all_count ?? 0),
    favorite: Number(row.favorite_count ?? 0),
    hidden: Number(row.hidden_count ?? 0),
    unreviewed: Number(row.unreviewed_count ?? 0),
  });
});

app.get("/api/v1/photos", async (req, res) => {
  if (STUB_MODE) {
    res.json({
      items: mockList,
      page: 1,
      pageSize: mockList.length,
      total: mockList.length,
      hasMore: false,
    });
    return;
  }

  const parsed = listQuerySchema.safeParse(req.query);
  if (!parsed.success) {
    res.status(400).json({ error: parsed.error.flatten() });
    return;
  }
  const query = parsed.data;

  const { whereSql, params } = buildPhotoFilters(query);

  const orderBy = getOrderBySql(query.sort);

  const queryEmbedding = query.q ? vectorLiteral(embedText(query.q)) : null;
  const listParams = queryEmbedding
    ? [...params, queryEmbedding, query.pageSize, (query.page - 1) * query.pageSize]
    : [...params, query.pageSize, (query.page - 1) * query.pageSize];
  const rankSelect = queryEmbedding
    ? `, (1 - (flm.description_embedding <=> $${params.length + 1}::vector)) AS semantic_rank`
    : ", NULL::double precision AS semantic_rank";
  const rankOrder = queryEmbedding
    ? `ORDER BY semantic_rank DESC NULLS LAST, ${orderBy}`
    : `ORDER BY ${orderBy}`;

  const sql = `
    SELECT
      f.id,
      f.source_root,
      f.relative_path,
      f.filename,
      f.photo_taken_at,
      f.camera_make,
      f.camera_model,
      fm.print_score_12x18,
      fm.print_score_8x10,
      fm.print_score_6x8,
      fm.curation_score,
      coalesce(flm.aesthetic_score, fm.aesthetic_score) AS aesthetic_score,
      coalesce(flm.description_text, fd.description_text) AS description_text,
      flm.wall_art_score,
      fl.keep_flag,
      fl.reject_flag,
      fl.favorite_flag
      ${rankSelect}
    FROM files f
    LEFT JOIN file_metrics fm ON fm.file_id = f.id
    LEFT JOIN file_descriptions fd ON fd.file_id = f.id
    LEFT JOIN file_labels fl ON fl.file_id = f.id
    LEFT JOIN file_llm_results flm ON flm.file_id = f.id
    ${whereSql}
    ${rankOrder}
    LIMIT $${params.length + (queryEmbedding ? 2 : 1)}
    OFFSET $${params.length + (queryEmbedding ? 3 : 2)}
  `;

  const countSql = `
    SELECT count(*)::int AS total
    FROM files f
    LEFT JOIN file_metrics fm ON fm.file_id = f.id
    LEFT JOIN file_descriptions fd ON fd.file_id = f.id
    LEFT JOIN file_labels fl ON fl.file_id = f.id
    LEFT JOIN file_llm_results flm ON flm.file_id = f.id
    ${whereSql}
  `;

  const [rows, countRows] = await Promise.all([pool.query(sql, listParams), pool.query(countSql, params)]);
  const total = Number(countRows.rows[0]?.total || 0);

  const items: PhotoListItem[] = (rows.rows as PhotoListRow[]).map((row) => ({
    id: row.id,
    sourceRoot: row.source_root,
    relativePath: row.relative_path,
    filename: row.filename,
    photoTakenAt: row.photo_taken_at ? new Date(row.photo_taken_at).toISOString() : null,
    cameraMake: row.camera_make,
    cameraModel: row.camera_model,
    printScore12x18: row.print_score_12x18,
    printScore8x10: row.print_score_8x10,
    printScore6x8: row.print_score_6x8,
    curationScore: row.curation_score,
    aestheticScore: row.aesthetic_score,
    descriptionText: row.description_text,
    wallArtScore: row.wall_art_score,
    keepFlag: row.keep_flag,
    rejectFlag: row.reject_flag,
    favoriteFlag: row.favorite_flag,
  }));

  res.json({
    items,
    page: query.page,
    pageSize: query.pageSize,
    total,
    hasMore: query.page * query.pageSize < total,
  });
});

app.get("/api/v1/photos/:id", async (req, res) => {
  const id = Number(req.params.id);
  if (!Number.isFinite(id)) {
    res.status(400).json({ error: "invalid id" });
    return;
  }

  if (STUB_MODE) {
    res.json(mockDetail(id));
    return;
  }

  const rows = await pool.query(
    `
      SELECT
        f.id, f.source_root, f.relative_path, f.filename, f.extension, f.width, f.height,
        f.photo_taken_at, f.photo_taken_at_source, f.camera_make, f.camera_model,
        coalesce(flm.description_text, fd.description_text) AS description_text,
        coalesce(flm.llm_payload_json, fd.description_json) AS description_json,
        fm.blur_score, fm.brightness_score, fm.contrast_score, fm.entropy_score, fm.noise_score,
        fm.technical_quality_score, fm.semantic_relevance_score, fm.curation_score,
        coalesce(flm.aesthetic_score, fm.aesthetic_score) AS aesthetic_score,
        flm.wall_art_score,
        fm.print_score_6x8, fm.print_score_8x10, fm.print_score_12x18,
        fl.keep_flag, fl.reject_flag, fl.favorite_flag,
        fl.print_candidate_6x8, fl.print_candidate_8x10, fl.print_candidate_12x18,
        fl.notes
      FROM files f
      LEFT JOIN file_descriptions fd ON fd.file_id = f.id
      LEFT JOIN file_metrics fm ON fm.file_id = f.id
      LEFT JOIN file_labels fl ON fl.file_id = f.id
      LEFT JOIN file_llm_results flm ON flm.file_id = f.id
      WHERE f.id = $1
    `,
    [id],
  );

  if (!rows.rowCount) {
    res.status(404).json({ error: "not found" });
    return;
  }

  const row = rows.rows[0];
  const detail: PhotoDetail = {
    id: row.id,
    sourceRoot: row.source_root,
    relativePath: row.relative_path,
    filename: row.filename,
    extension: row.extension,
    width: row.width,
    height: row.height,
    photoTakenAt: row.photo_taken_at ? new Date(row.photo_taken_at).toISOString() : null,
    photoTakenAtSource: row.photo_taken_at_source,
    cameraMake: row.camera_make,
    cameraModel: row.camera_model,
    descriptionText: row.description_text,
    descriptionJson: row.description_json,
    metrics: {
      blurScore: row.blur_score,
      brightnessScore: row.brightness_score,
      contrastScore: row.contrast_score,
      entropyScore: row.entropy_score,
      noiseScore: row.noise_score,
      technicalQualityScore: row.technical_quality_score,
      semanticRelevanceScore: row.semantic_relevance_score,
      curationScore: row.curation_score,
      aestheticScore: row.aesthetic_score,
      wallArtScore: row.wall_art_score,
      printScore6x8: row.print_score_6x8,
      printScore8x10: row.print_score_8x10,
      printScore12x18: row.print_score_12x18,
    },
    labels: {
      keepFlag: row.keep_flag,
      rejectFlag: row.reject_flag,
      favoriteFlag: row.favorite_flag,
      printCandidate6x8: row.print_candidate_6x8,
      printCandidate8x10: row.print_candidate_8x10,
      printCandidate12x18: row.print_candidate_12x18,
      notes: row.notes,
    },
  };

  res.json(detail);
});

app.patch("/api/v1/photos/:id/labels", async (req, res) => {
  const id = Number(req.params.id);
  if (!Number.isFinite(id)) {
    res.status(400).json({ error: "invalid id" });
    return;
  }

  const parsed = labelPatchSchema.safeParse(req.body as LabelPatch);
  if (!parsed.success) {
    res.status(400).json({ error: parsed.error.flatten() });
    return;
  }

  if (STUB_MODE) {
    res.json({ ok: true, stubMode: true });
    return;
  }

  const body = parsed.data;

  await pool.query(
    `
      INSERT INTO file_labels (
        file_id, keep_flag, reject_flag, favorite_flag,
        print_candidate_6x8, print_candidate_8x10, print_candidate_12x18,
        notes
      ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
      ON CONFLICT (file_id) DO UPDATE SET
        keep_flag = COALESCE(EXCLUDED.keep_flag, file_labels.keep_flag),
        reject_flag = COALESCE(EXCLUDED.reject_flag, file_labels.reject_flag),
        favorite_flag = COALESCE(EXCLUDED.favorite_flag, file_labels.favorite_flag),
        print_candidate_6x8 = COALESCE(EXCLUDED.print_candidate_6x8, file_labels.print_candidate_6x8),
        print_candidate_8x10 = COALESCE(EXCLUDED.print_candidate_8x10, file_labels.print_candidate_8x10),
        print_candidate_12x18 = COALESCE(EXCLUDED.print_candidate_12x18, file_labels.print_candidate_12x18),
        notes = COALESCE(EXCLUDED.notes, file_labels.notes),
        updated_at = now()
    `,
    [
      id,
      body.keepFlag ?? null,
      body.rejectFlag ?? null,
      body.favoriteFlag ?? null,
      body.printCandidate6x8 ?? null,
      body.printCandidate8x10 ?? null,
      body.printCandidate12x18 ?? null,
      body.notes ?? null,
    ],
  );

  res.json({ ok: true });
});

function sanitizeContentDispositionFilename(filename: string): string {
  return filename.replace(/[\r\n\\"]/g, "_");
}

app.get("/api/v1/photos/:id/image", async (req, res) => {
  const id = Number(req.params.id);
  if (!Number.isFinite(id)) {
    res.status(400).json({ error: "invalid id" });
    return;
  }

  const size = req.query.size === "thumb" ? "thumb" : "full";

  if (STUB_MODE) {
    const stubPath = path.resolve("reference/stub-photo.svg");
    if (fs.existsSync(stubPath)) {
      res.sendFile(stubPath);
      return;
    }
  }

  const rows = await pool.query("SELECT source_root, relative_path, filename, sha256 FROM files WHERE id = $1", [id]);
  if (!rows.rowCount) {
    res.status(404).json({ error: "not found" });
    return;
  }

  const row = rows.rows[0];
  const requestedName = typeof req.query.downloadName === "string" ? req.query.downloadName : row.filename;
  const fallbackName = typeof row.filename === "string" && row.filename.trim() ? row.filename : "image";
  const safeName = sanitizeContentDispositionFilename(String(requestedName || fallbackName));
  res.setHeader("Content-Disposition", `inline; filename=\"${safeName}\"`);
  if (size === "thumb") {
    const thumbDir = process.env.THUMBS_DIR || "/data/cache/thumbs";
    const thumbPath = path.join(thumbDir, `${row.sha256}.jpg`);
    if (fs.existsSync(thumbPath)) {
      res.sendFile(thumbPath);
      return;
    }
  }

  const fullPath = resolveFilePath(row.source_root, row.relative_path);
  res.sendFile(fullPath);
});

app.get("/api/v1/facets", async (_req, res) => {
  if (STUB_MODE) {
    res.json({
      camera: [{ camera_make: "Canon", camera_model: "EOS R6", count: 2 }],
      categories: [{ category: "people", count: 2 }],
      statuses: { keep: 1, favorite: 1, reject: 0, unreviewed: 1 },
      dateBounds: { min: "2024-06-10", max: "2024-06-11" },
    });
    return;
  }

  const [camera, statuses, categories, dateBounds] = await Promise.all([
    pool.query(
      "SELECT camera_make, camera_model, count(*)::int AS count FROM files GROUP BY camera_make, camera_model ORDER BY count DESC",
    ),
    pool.query(
      `
      SELECT
        count(*) FILTER (WHERE fl.keep_flag = true)::int AS keep,
        count(*) FILTER (WHERE fl.favorite_flag = true)::int AS favorite,
        count(*) FILTER (WHERE fl.reject_flag = true)::int AS reject,
        count(*) FILTER (WHERE fl.file_id IS NULL)::int AS unreviewed
      FROM files f
      LEFT JOIN file_labels fl ON fl.file_id = f.id
    `,
    ),
    pool.query(
      `
      SELECT category, count(*)::int AS count
      FROM (
        SELECT jsonb_array_elements_text(coalesce(fd.description_json->'categories', '[]'::jsonb)) AS category
        FROM file_descriptions fd
        UNION ALL
        SELECT unnest(coalesce(flm.tags, ARRAY[]::text[])) AS category
        FROM file_llm_results flm
      ) categories
      GROUP BY category
      ORDER BY count DESC, category ASC
      LIMIT 30
    `,
    ),
    pool.query(
      `
      SELECT
        min(photo_taken_at)::timestamptz AS min_taken_at,
        max(photo_taken_at)::timestamptz AS max_taken_at
      FROM files
      WHERE photo_taken_at IS NOT NULL
    `,
    ),
  ]);

  const bounds = dateBounds.rows[0];
  res.json({
    camera: camera.rows,
    categories: categories.rows,
    statuses: statuses.rows[0] ?? {},
    dateBounds: {
      min: bounds?.min_taken_at ? new Date(bounds.min_taken_at).toISOString().slice(0, 10) : null,
      max: bounds?.max_taken_at ? new Date(bounds.max_taken_at).toISOString().slice(0, 10) : null,
    },
  });
});

const port = Number(process.env.PORT || 3001);
app.listen(port, () => {
  console.log(`API listening on ${port} (stub mode: ${STUB_MODE})`);
});
