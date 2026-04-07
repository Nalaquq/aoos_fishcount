"""SQLite logging for fish counts and system health."""

from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path


class Database:
    """Manages the SQLite count and health log database."""

    def __init__(self, db_path: str | Path) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self._create_tables()

    def _create_tables(self) -> None:
        self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS counts (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                direction TEXT NOT NULL DEFAULT 'upstream',
                species   TEXT,
                confidence REAL,
                track_id  INTEGER
            );
            CREATE TABLE IF NOT EXISTS health (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp    TEXT NOT NULL,
                temp_c       REAL,
                humidity_pct REAL,
                cpu_temp_c   REAL
            );
        """)
        self._conn.commit()

    def log_count(
        self,
        species: str,
        confidence: float,
        track_id: int,
        direction: str = "upstream",
    ) -> None:
        """Record a fish crossing event."""
        self._conn.execute(
            "INSERT INTO counts (timestamp, direction, species, confidence, track_id) "
            "VALUES (?, ?, ?, ?, ?)",
            (datetime.now().isoformat(), direction, species, confidence, track_id),
        )
        self._conn.commit()

    def log_health(
        self,
        temp_c: float | None,
        humidity_pct: float | None,
        cpu_temp_c: float | None = None,
    ) -> None:
        """Record an interior environment health reading."""
        self._conn.execute(
            "INSERT INTO health (timestamp, temp_c, humidity_pct, cpu_temp_c) "
            "VALUES (?, ?, ?, ?)",
            (datetime.now().isoformat(), temp_c, humidity_pct, cpu_temp_c),
        )
        self._conn.commit()

    def hourly_summary(self) -> dict:
        """Return per-species counts and latest health for the past hour."""
        rows = self._conn.execute(
            "SELECT species, COUNT(*) FROM counts "
            "WHERE timestamp > datetime('now', '-1 hour') "
            "GROUP BY species"
        ).fetchall()
        counts = {row[0]: row[1] for row in rows}

        health = self._conn.execute(
            "SELECT temp_c, humidity_pct, cpu_temp_c FROM health "
            "ORDER BY id DESC LIMIT 1"
        ).fetchone()

        return {
            "counts": counts,
            "interior_temp_c": health[0] if health else None,
            "interior_rh_pct": health[1] if health else None,
            "cpu_temp_c": health[2] if health else None,
        }

    def close(self) -> None:
        self._conn.close()
