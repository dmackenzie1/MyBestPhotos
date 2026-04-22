import { Pool } from "pg";

const pool = new Pool({
  connectionString:
    process.env.DATABASE_URL ||
    "postgresql://photo_curator:photo_curator@postgres:5432/photo_curator",
});

pool.on("error", (err: Error) => {
  process.stderr.write(`[db] Unexpected pool error: ${err.message}\n`);
});

export default pool;

export async function checkHealth(): Promise<{ ok: boolean; error?: string }> {
  try {
    const result = await pool.query("SELECT 1 AS health_check");
    return { ok: result.rows.length > 0 };
  } catch (err) {
    return { ok: false, error: err instanceof Error ? err.message : String(err) };
  }
}
