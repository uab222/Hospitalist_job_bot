"""SQLite-backed storage: dedupes postings across runs and tracks their
status as you review/approve/apply to them."""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path

from .config import DEFAULT_DB_PATH
from .models import STATUS_NEW, JobPosting

SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
    job_id TEXT PRIMARY KEY,
    source TEXT NOT NULL,
    source_id TEXT NOT NULL,
    title TEXT NOT NULL,
    employer TEXT NOT NULL,
    location TEXT NOT NULL,
    url TEXT NOT NULL,
    description TEXT,
    employment_type TEXT,
    apply_email TEXT,
    posted_at TEXT,
    score INTEGER,
    match_reasons TEXT,
    cover_letter TEXT,
    status TEXT NOT NULL DEFAULT 'new',
    first_seen_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);
"""


class JobStore:
    def __init__(self, db_path: Path = DEFAULT_DB_PATH):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.execute(SCHEMA)

    @contextmanager
    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def upsert(self, posting: JobPosting) -> bool:
        """Inserts a new posting, or updates score/reasons on an existing one
        without touching its status. Returns True if this was a new posting."""
        with self._connect() as conn:
            existing = conn.execute(
                "SELECT job_id FROM jobs WHERE job_id = ?", (posting.job_id,)
            ).fetchone()

            if existing:
                conn.execute(
                    """UPDATE jobs SET score = ?, match_reasons = ?, updated_at = CURRENT_TIMESTAMP
                       WHERE job_id = ?""",
                    (posting.score, json.dumps(posting.match_reasons), posting.job_id),
                )
                return False

            conn.execute(
                """INSERT INTO jobs (
                    job_id, source, source_id, title, employer, location, url,
                    description, employment_type, apply_email, posted_at,
                    score, match_reasons, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    posting.job_id,
                    posting.source,
                    posting.source_id,
                    posting.title,
                    posting.employer,
                    posting.location,
                    posting.url,
                    posting.description,
                    posting.employment_type,
                    posting.apply_email,
                    posting.posted_at,
                    posting.score,
                    json.dumps(posting.match_reasons),
                    STATUS_NEW,
                ),
            )
            return True

    def set_apply_email(self, job_id: str, apply_email: str) -> None:
        with self._connect() as conn:
            conn.execute(
                "UPDATE jobs SET apply_email = ?, updated_at = CURRENT_TIMESTAMP WHERE job_id = ?",
                (apply_email, job_id),
            )

    def set_cover_letter(self, job_id: str, cover_letter: str) -> None:
        with self._connect() as conn:
            conn.execute(
                "UPDATE jobs SET cover_letter = ?, updated_at = CURRENT_TIMESTAMP WHERE job_id = ?",
                (cover_letter, job_id),
            )

    def set_status(self, job_id: str, status: str) -> None:
        with self._connect() as conn:
            conn.execute(
                "UPDATE jobs SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE job_id = ?",
                (status, job_id),
            )

    def get(self, job_id: str) -> sqlite3.Row | None:
        with self._connect() as conn:
            return conn.execute("SELECT * FROM jobs WHERE job_id = ?", (job_id,)).fetchone()

    def list_by_status(self, status: str | None = None) -> list:
        with self._connect() as conn:
            if status:
                rows = conn.execute(
                    "SELECT * FROM jobs WHERE status = ? ORDER BY score DESC", (status,)
                ).fetchall()
            else:
                rows = conn.execute("SELECT * FROM jobs ORDER BY score DESC").fetchall()
            return [dict(row) for row in rows]
