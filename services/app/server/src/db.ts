import { Pool } from "pg";

const pool = new Pool({
  connectionString:
    process.env.DATABASE_URL ||
    "postgresql://photo_curator:photo_curator@db:5432/photo_curator",
});

export default pool;
