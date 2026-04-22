import cors from "cors";
import express from "express";
import path from "node:path";
import fs from "node:fs";
import { z } from "zod";
import type { LabelPatch, PhotoDetail, PhotoListItem } from "@mybestphotos/shared";
import pool from "./db.js";

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

const listQuerySchema = z.object({
  q: z.string().optional(),
  dateFrom: z.string().optional(),
  dateTo: z.string().optional(),
  cameraMake: z.string().optional(),
  minPrintScore12x18: z.coerce.number().optional(),
  status: z.enum(["all", "keep", "favorite", "reject", "unreviewed"]).default("all"),
  page: z.coerce.number().min(1).default(1),
  pageSize: z.coerce.number().min(1).max(200).default(40),
  sort: z.enum(["date_desc", "date_asc", "print_12x18_desc", "filename_asc"]).default("date_desc"),
});

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
  description_text: string | null;
  keep_flag: boolean | null;
  reject_flag: boolean | null;
  favorite_flag: boolean | null;
};
// Intent note: explicit row typing here fixes TS7006
// ("Parameter 'row' implicitly has an 'any' type") during app-server builds.

function resolveFilePath(sourceRoot: string, relativePath: string): string {
  const root = path.resolve(sourceRoot);
  const full = path.resolve(root, relativePath);
  if (!full.startsWith(root)) {
    throw new Error("Unsafe file path");
  }
  return full;
}

app.get("/api/v1/health", (_req, res) => {
  res.json({ ok: true, stubMode: STUB_MODE });
});

app.get("/api/v1/photos", async (req, res) => {
  if (STUB_MODE) {
    res.json({ items: mockList, page: 1, pageSize: mockList.length });
    return;
  }

  const parsed = listQuerySchema.safeParse(req.query);
  if (!parsed.success) {
    res.status(400).json({ error: parsed.error.flatten() });
    return;
  }
  const query = parsed.data;

  const where: string[] = [];
  const params: Array<string | number> = [];

  if (query.q) {
    params.push(query.q);
    where.push(`to_tsvector('english', coalesce(fd.description_text, '')) @@ plainto_tsquery('english', $${params.length})`);
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
  if (typeof query.minPrintScore12x18 === "number") {
    params.push(query.minPrintScore12x18);
    where.push(`coalesce(fm.print_score_12x18, 0) >= $${params.length}`);
  }

  if (query.status === "keep") where.push("fl.keep_flag = true");
  if (query.status === "favorite") where.push("fl.favorite_flag = true");
  if (query.status === "reject") where.push("fl.reject_flag = true");
  if (query.status === "unreviewed") where.push("fl.file_id is null");

  const whereSql = where.length ? `WHERE ${where.join(" AND ")}` : "";

  const orderBy =
    query.sort === "date_asc"
      ? "f.photo_taken_at ASC NULLS LAST"
      : query.sort === "print_12x18_desc"
        ? "fm.print_score_12x18 DESC NULLS LAST"
        : query.sort === "filename_asc"
          ? "f.filename ASC"
          : "f.photo_taken_at DESC NULLS LAST";

  params.push(query.pageSize);
  const limitIdx = params.length;
  params.push((query.page - 1) * query.pageSize);
  const offsetIdx = params.length;

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
      fd.description_text,
      fl.keep_flag,
      fl.reject_flag,
      fl.favorite_flag
    FROM files f
    LEFT JOIN file_metrics fm ON fm.file_id = f.id
    LEFT JOIN file_descriptions fd ON fd.file_id = f.id
    LEFT JOIN file_labels fl ON fl.file_id = f.id
    ${whereSql}
    ORDER BY ${orderBy}
    LIMIT $${limitIdx}
    OFFSET $${offsetIdx}
  `;

  const rows = await pool.query(sql, params);
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
    descriptionText: row.description_text,
    keepFlag: row.keep_flag,
    rejectFlag: row.reject_flag,
    favoriteFlag: row.favorite_flag,
  }));

  res.json({ items, page: query.page, pageSize: query.pageSize });
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
        fd.description_text, fd.description_json,
        fm.blur_score, fm.brightness_score, fm.contrast_score, fm.entropy_score, fm.noise_score,
        fm.print_score_6x8, fm.print_score_8x10, fm.print_score_12x18,
        fl.keep_flag, fl.reject_flag, fl.favorite_flag,
        fl.print_candidate_6x8, fl.print_candidate_8x10, fl.print_candidate_12x18,
        fl.notes
      FROM files f
      LEFT JOIN file_descriptions fd ON fd.file_id = f.id
      LEFT JOIN file_metrics fm ON fm.file_id = f.id
      LEFT JOIN file_labels fl ON fl.file_id = f.id
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

app.get("/api/v1/photos/:id/image", async (req, res) => {
  const id = Number(req.params.id);
  const size = req.query.size === "thumb" ? "thumb" : "full";

  if (STUB_MODE) {
    const stubPath = path.resolve("reference/stub-photo.svg");
    if (fs.existsSync(stubPath)) {
      res.sendFile(stubPath);
      return;
    }
  }

  const rows = await pool.query("SELECT source_root, relative_path, sha256 FROM files WHERE id = $1", [id]);
  if (!rows.rowCount) {
    res.status(404).json({ error: "not found" });
    return;
  }

  const row = rows.rows[0];
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
      camera: [{ camera_make: "Canon", count: 2 }],
      statuses: { keep: 1, favorite: 1, reject: 0, unreviewed: 1 },
    });
    return;
  }

  const camera = await pool.query(
    "SELECT camera_make, count(*)::int AS count FROM files GROUP BY camera_make ORDER BY count DESC",
  );
  const statuses = await pool.query(
    `
      SELECT
        count(*) FILTER (WHERE fl.keep_flag = true)::int AS keep,
        count(*) FILTER (WHERE fl.favorite_flag = true)::int AS favorite,
        count(*) FILTER (WHERE fl.reject_flag = true)::int AS reject,
        count(*) FILTER (WHERE fl.file_id IS NULL)::int AS unreviewed
      FROM files f
      LEFT JOIN file_labels fl ON fl.file_id = f.id
    `,
  );
  res.json({ camera: camera.rows, statuses: statuses.rows[0] ?? {} });
});

const port = Number(process.env.PORT || 3001);
app.listen(port, () => {
  console.log(`API listening on ${port} (stub mode: ${STUB_MODE})`);
});
