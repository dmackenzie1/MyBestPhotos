from __future__ import annotations

from pathlib import Path
import csv
import shutil

from loguru import logger

from photo_curator.db import Database


def export_reports(
    db: Database,
    run_id: int,
    report_dir: str,
    thumbs_dir: str,
    output_dir: str | None = None,
    copy_files: bool = False,
    link_files: bool = False,
) -> None:
    rows = db.fetchall(
        """
        SELECT s.rank, p.id, p.path, p.sha256, s.final_score
        FROM selections s
        JOIN photos p ON p.id = s.photo_id
        WHERE s.run_id = %s
        ORDER BY s.rank ASC
        """,
        (run_id,),
    )

    report_path = Path(report_dir)
    report_path.mkdir(parents=True, exist_ok=True)

    csv_path = report_path / "report.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["rank", "photo_id", "path", "score"])
        for rank, photo_id, path, _sha256, score in rows:
            writer.writerow([rank, photo_id, path, f"{score:.4f}"])

    html_path = report_path / "gallery.html"
    with html_path.open("w", encoding="utf-8") as handle:
        handle.write("<html><head><meta charset='utf-8'><title>Photo Curator</title>")
        handle.write("<style>body{font-family:sans-serif;} .grid{display:flex;flex-wrap:wrap;gap:12px;} .card{width:200px;}</style>")
        handle.write("</head><body><h1>Photo Curator Results</h1><div class='grid'>")
        for rank, _photo_id, path, sha256, score in rows:
            thumb_path = Path(thumbs_dir) / f"{sha256}.jpg"
            handle.write("<div class='card'>")
            if thumb_path.exists():
                handle.write(f"<img src='../{thumb_path.as_posix()}' width='200' /><br/>")
            handle.write(f"<strong>#{rank}</strong><br/>")
            handle.write(f"<small>{path}</small><br/>")
            handle.write(f"<small>Score: {score:.3f}</small>")
            handle.write("</div>")
        handle.write("</div></body></html>")

    if output_dir and (copy_files or link_files):
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        for rank, _photo_id, path, _sha256, _score in rows:
            dest = output_path / f"{rank:04d}_{Path(path).name}"
            if link_files:
                if dest.exists():
                    dest.unlink()
                dest.symlink_to(path)
            else:
                shutil.copy2(path, dest)

    logger.info("Reports written to {path}", path=report_path)
