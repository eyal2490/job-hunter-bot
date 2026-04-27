"""
Lightweight SQLite-based deduplication store.

We keep a single table of job IDs (hashed) we've already seen and notified about.
This prevents the bot from spamming Telegram with the same job twice.
"""

import sqlite3
import hashlib
from datetime import datetime
from config import DB_PATH


def _conn():
    return sqlite3.connect(DB_PATH)


def init_db():
    """Create the table if it doesn't exist."""
    with _conn() as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS seen_jobs (
                job_hash TEXT PRIMARY KEY,
                company TEXT,
                title TEXT,
                url TEXT,
                first_seen TEXT
            )
        """)
        c.commit()


def make_hash(company, url, title):
    """Stable hash that uniquely identifies a job posting."""
    raw = f"{company}|{url}|{title}".lower()
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]


def is_seen(job_hash):
    with _conn() as c:
        cur = c.execute("SELECT 1 FROM seen_jobs WHERE job_hash = ?", (job_hash,))
        return cur.fetchone() is not None


def mark_seen(job_hash, company, title, url):
    with _conn() as c:
        c.execute(
            "INSERT OR IGNORE INTO seen_jobs (job_hash, company, title, url, first_seen) VALUES (?, ?, ?, ?, ?)",
            (job_hash, company, title, url, datetime.utcnow().isoformat()),
        )
        c.commit()


def count_seen():
    with _conn() as c:
        cur = c.execute("SELECT COUNT(*) FROM seen_jobs")
        return cur.fetchone()[0]
