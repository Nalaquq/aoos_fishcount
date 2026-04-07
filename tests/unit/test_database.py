"""Unit tests for Database."""

import pytest
from aoos_fishcount.utils.database import Database


def test_log_count(tmp_db):
    tmp_db.log_count("chinook", 0.82, track_id=42)
    summary = tmp_db.hourly_summary()
    assert summary.get("chinook") == 1


def test_log_health(tmp_db):
    tmp_db.log_health(temp_c=18.5, humidity_pct=45.2)
    row = tmp_db._conn.execute(
        "SELECT temp_c, humidity_pct FROM health LIMIT 1"
    ).fetchone()
    assert row == (18.5, 45.2)


def test_hourly_summary_multiple_species(tmp_db):
    tmp_db.log_count("chinook", 0.9, 1)
    tmp_db.log_count("chinook", 0.85, 2)
    tmp_db.log_count("coho", 0.75, 3)
    summary = tmp_db.hourly_summary()
    assert summary["chinook"] == 2
    assert summary["coho"] == 1


def test_db_creates_parent_dir(tmp_path):
    nested = tmp_path / "deep" / "nested" / "test.db"
    db = Database(nested)
    assert nested.exists()
    db.close()
