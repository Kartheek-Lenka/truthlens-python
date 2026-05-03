"""
database/db.py — SQLite Persistence Layer
Stores analysis history in a local SQLite database.
"""

import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, TypedDict

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import DB_PATH

logger = logging.getLogger(__name__)


# ── Row Schema ─────────────────────────────────────────────────────────────────

class AnalysisLog(TypedDict):
    id: int
    timestamp: str
    isFake: bool
    confidence: int
    reasoning: str
    engine: str
    cpu_time: str
    memory: str


# ── DB Setup ───────────────────────────────────────────────────────────────────

def _get_connection() -> sqlite3.Connection:
    """Open (and create if needed) the SQLite database file."""
    db_file = Path(DB_PATH)
    db_file.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_file))
    conn.row_factory = sqlite3.Row   # Allow dict-style access to rows
    return conn


def init_db() -> None:
    """
    Create the analysis_logs table if it does not yet exist.
    Safe to call multiple times (idempotent).
    """
    conn = _get_connection()
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS analysis_logs (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp  TEXT    NOT NULL,
                isFake     INTEGER NOT NULL,   -- SQLite stores booleans as 0/1
                confidence INTEGER NOT NULL,
                reasoning  TEXT    NOT NULL,
                engine     TEXT    NOT NULL DEFAULT 'local',
                cpu_time   TEXT    NOT NULL DEFAULT '',
                memory     TEXT    NOT NULL DEFAULT ''
            )
        """)
        conn.commit()
        logger.debug("Database initialised at %s", DB_PATH)
    finally:
        conn.close()


# ── CRUD ───────────────────────────────────────────────────────────────────────

def save_result(
    is_fake: bool,
    confidence: int,
    reasoning: str,
    engine: str = "local",
    cpu_time: str = "",
    memory: str = "",
) -> int:
    """
    Persist one analysis result to the database.

    Args:
        is_fake:    Whether the frame was classified as manipulated.
        confidence: Confidence score (0–100).
        reasoning:  Textual explanation from the inference engine.
        engine:     Which engine produced the result ("gemini" / "local" / …).
        cpu_time:   Human-readable inference duration string.
        memory:     Human-readable process RSS string.

    Returns:
        The auto-assigned row id.
    """
    conn = _get_connection()
    try:
        cursor = conn.execute(
            """
            INSERT INTO analysis_logs
                (timestamp, isFake, confidence, reasoning, engine, cpu_time, memory)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                datetime.utcnow().isoformat(timespec="seconds") + "Z",
                int(is_fake),
                confidence,
                reasoning,
                engine,
                cpu_time,
                memory,
            ),
        )
        conn.commit()
        row_id: int = cursor.lastrowid  # type: ignore[assignment]
        logger.debug("Saved analysis result with id=%d", row_id)
        return row_id
    finally:
        conn.close()


def get_history(limit: int = 50) -> List[AnalysisLog]:
    """
    Retrieve recent analysis logs, newest first.

    Args:
        limit: Maximum number of rows to return.

    Returns:
        List of AnalysisLog dicts.
    """
    conn = _get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM analysis_logs ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
        results: List[AnalysisLog] = []
        for row in rows:
            results.append(
                AnalysisLog(
                    id=row["id"],
                    timestamp=row["timestamp"],
                    isFake=bool(row["isFake"]),
                    confidence=row["confidence"],
                    reasoning=row["reasoning"],
                    engine=row["engine"],
                    cpu_time=row["cpu_time"],
                    memory=row["memory"],
                )
            )
        return results
    finally:
        conn.close()


def clear_history() -> None:
    """Delete all rows from analysis_logs (dev/testing utility)."""
    conn = _get_connection()
    try:
        conn.execute("DELETE FROM analysis_logs")
        conn.commit()
        logger.warning("All analysis history cleared.")
    finally:
        conn.close()


# ── Auto-initialise on import ──────────────────────────────────────────────────
init_db()
