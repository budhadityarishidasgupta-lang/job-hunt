import sqlite3
from datetime import datetime
from typing import Dict, List, Tuple

DB_PATH = "feedback.db"


def _get_conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)


def init_db():
    """Create the feedback table if it does not exist."""
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_title TEXT,
            company TEXT,
            source TEXT,
            location TEXT,
            url TEXT,
            emb_score REAL,
            feedback INTEGER,  -- +1 or -1
            created_at TEXT
        );
        """
    )
    conn.commit()
    conn.close()


def save_feedback(job: Dict, feedback: int):
    """Save user feedback: +1 relevant, -1 irrelevant."""
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO feedback (job_title, company, source, location, url, emb_score, feedback, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            job.get("title", ""),
            job.get("company", ""),
            job.get("source", ""),
            job.get("location", ""),
            job.get("url", ""),
            float(job.get("score", 0.0)),
            int(feedback),
            datetime.utcnow().isoformat(),
        ),
    )
    conn.commit()
    conn.close()


def get_feedback_examples(limit: int = 3) -> Tuple[List[str], List[str]]:
    """
    Return two lists:
      liked_titles    – recently liked jobs
      disliked_titles – recently disliked jobs
    """
    conn = _get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT job_title, source
        FROM feedback
        WHERE feedback = 1
        ORDER BY created_at DESC
        LIMIT ?
        """,
        (limit,),
    )
    liked_rows = cur.fetchall()

    cur.execute(
        """
        SELECT job_title, source
        FROM feedback
        WHERE feedback = -1
        ORDER BY created_at DESC
        LIMIT ?
        """,
        (limit,),
    )
    disliked_rows = cur.fetchall()

    conn.close()

    liked = [f"{title} ({src})" for (title, src) in liked_rows]
    disliked = [f"{title} ({src})" for (title, src) in disliked_rows]

    return liked, disliked

