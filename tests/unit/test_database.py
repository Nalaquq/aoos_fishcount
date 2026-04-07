"""Unit tests for Database."""

import pytest
from aoos_fishcount.utils.database import Database


def test_log_count(tmp_db):
    tmp_db.log_count("chinook", 0.82, track_id=42)
    summary = tmp_db.hourly_summary()
    assert summary["counts"].get("chinook") == 1


def test_log_health(tmp_db):
    tmp_db.log_health(temp_c=18.5, humidity_pct=45.2, cpu_temp_c=52.3)
    row = tmp_db._conn.execute(
        "SELECT temp_c, humidity_pct, cpu_temp_c FROM health LIMIT 1"
    ).fetchone()
    assert row == (18.5, 45.2, 52.3)


def test_hourly_summary_multiple_species(tmp_db):
    tmp_db.log_count("chinook", 0.9, 1)
    tmp_db.log_count("chinook", 0.85, 2)
    tmp_db.log_count("coho", 0.75, 3)
    summary = tmp_db.hourly_summary()
    assert summary["counts"]["chinook"] == 2
    assert summary["counts"]["coho"] == 1


def test_hourly_summary_includes_health(tmp_db):
    tmp_db.log_health(temp_c=20.0, humidity_pct=55.0, cpu_temp_c=48.0)
    summary = tmp_db.hourly_summary()
    assert summary["interior_temp_c"] == 20.0
    assert summary["interior_rh_pct"] == 55.0
    assert summary["cpu_temp_c"] == 48.0


def test_hourly_summary_no_health(tmp_db):
    summary = tmp_db.hourly_summary()
    assert summary["interior_temp_c"] is None
    assert summary["interior_rh_pct"] is None


def test_db_creates_parent_dir(tmp_path):
    nested = tmp_path / "deep" / "nested" / "test.db"
    db = Database(nested)
    assert nested.exists()
    db.close()
