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
