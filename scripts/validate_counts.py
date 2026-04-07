#!/usr/bin/env python3
"""Compare CV counts against human observer tallies for validation.

Calculates the metrics required before KRITFC / ADF&G can use the data:
  - Detection Efficiency  (CV count / observer count)
  - Species Classification Accuracy
  - False Positive Rate
  - System Uptime

Usage:
    python scripts/validate_counts.py --db data/counts/fishcount.db \
        --observer observer_tallies.csv

Observer CSV format (one row per hour):
    start_time,end_time,chinook,chum,coho,sockeye,pink,false_positives
    2026-06-15T06:00,2026-06-15T07:00,12,45,3,0,0,2
"""

import argparse
import csv
import sqlite3
import sys
from datetime import datetime
from pathlib import Path


def load_observer_data(csv_path: Path) -> list[dict]:
    """Load observer tallies from CSV."""
    rows = []
    with csv_path.open() as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


def query_cv_counts(db_path: Path, start: str, end: str) -> dict[str, int]:
    """Query CV species counts between start and end timestamps."""
    conn = sqlite3.connect(str(db_path))
    rows = conn.execute(
        "SELECT species, COUNT(*) FROM counts "
        "WHERE timestamp >= ? AND timestamp < ? AND direction = 'upstream' "
        "GROUP BY species",
        (start, end),
    ).fetchall()
    conn.close()
    return {r[0]: r[1] for r in rows}


def query_system_uptime(db_path: Path, start: str, end: str) -> float:
    """Estimate uptime as fraction of 5-min health intervals that have data."""
    conn = sqlite3.connect(str(db_path))
    count = conn.execute(
        "SELECT COUNT(*) FROM health WHERE timestamp >= ? AND timestamp < ?",
        (start, end),
    ).fetchone()[0]
    conn.close()

    start_dt = datetime.fromisoformat(start)
    end_dt = datetime.fromisoformat(end)
    hours = (end_dt - start_dt).total_seconds() / 3600
    expected_readings = hours * 12  # one every 5 minutes
    if expected_readings == 0:
        return 0.0
    return min(count / expected_readings, 1.0)


SPECIES = ["chinook", "chum", "coho", "sockeye", "pink"]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate CV counts against observer tallies"
    )
    parser.add_argument("--db", type=Path, required=True,
                        help="Path to SQLite fishcount database")
    parser.add_argument("--observer", type=Path, required=True,
                        help="Path to observer tallies CSV")
    args = parser.parse_args()

    if not args.db.exists():
        print(f"Database not found: {args.db}", file=sys.stderr)
        return 1
    if not args.observer.exists():
        print(f"Observer CSV not found: {args.observer}", file=sys.stderr)
        return 1

    observer_rows = load_observer_data(args.observer)

    total_observer = 0
    total_cv = 0
    species_correct = 0
    species_total = 0
    total_false_positives = 0
    total_cv_detections = 0

    print("=" * 70)
    print("  Salmon CV Validation Report")
    print("=" * 70)
    print(f"  Database:  {args.db}")
    print(f"  Observer:  {args.observer}")
    print(f"  Periods:   {len(observer_rows)}")
    print("=" * 70)

    for row in observer_rows:
        start = row["start_time"]
        end = row["end_time"]
        cv_counts = query_cv_counts(args.db, start, end)
        cv_total = sum(cv_counts.values())
        obs_total = sum(int(row.get(s, 0)) for s in SPECIES)
        fp = int(row.get("false_positives", 0))

        total_observer += obs_total
        total_cv += cv_total
        total_false_positives += fp
        total_cv_detections += cv_total + fp

        # Species accuracy: compare per-species counts
        for sp in SPECIES:
            obs_sp = int(row.get(sp, 0))
            cv_sp = cv_counts.get(sp, 0)
            matched = min(obs_sp, cv_sp)
            species_correct += matched
            species_total += obs_sp

        print(f"\n  {start} — {end}")
        print(f"    Observer: {obs_total}  CV: {cv_total}  "
              f"Efficiency: {cv_total / obs_total:.2f}" if obs_total > 0 else
              f"    Observer: {obs_total}  CV: {cv_total}")

    # Overall start/end for uptime calc
    if observer_rows:
        overall_start = observer_rows[0]["start_time"]
        overall_end = observer_rows[-1]["end_time"]
        uptime = query_system_uptime(args.db, overall_start, overall_end)
    else:
        uptime = 0.0

    print("\n" + "=" * 70)
    print("  SUMMARY METRICS")
    print("=" * 70)

    if total_observer > 0:
        det_eff = total_cv / total_observer
        print(f"  Detection Efficiency:       {det_eff:.2f}  "
              f"(target > 0.80)")
    else:
        det_eff = 0.0
        print(f"  Detection Efficiency:       N/A (no observer counts)")

    if species_total > 0:
        sp_acc = species_correct / species_total
        print(f"  Species Classification:     {sp_acc:.2f}  "
              f"(target > 0.85 for sockeye, coho)")
    else:
        print(f"  Species Classification:     N/A")

    if total_cv_detections > 0:
        fp_rate = total_false_positives / total_cv_detections
        print(f"  False Positive Rate:        {fp_rate:.3f}  "
              f"(target < 0.05)")
    else:
        print(f"  False Positive Rate:        N/A")

    print(f"  System Uptime:              {uptime:.2f}  "
          f"(target > 0.95)")
    print(f"  Total Observer Count:       {total_observer}")
    print(f"  Total CV Count:             {total_cv}")

    if total_observer > 0 and det_eff > 0:
        margin = 1.96 * ((det_eff * (1 - det_eff)) / total_observer) ** 0.5
        print(f"\n  Reporting format:")
        print(f"  'CV-estimated count: {total_cv} +/- {margin * 100:.0f}% "
              f"(based on {det_eff:.2f} detection efficiency")
        print(f"   measured against {len(observer_rows)} hours of concurrent "
              f"observer counts, 95% CI)'")

    print("=" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(main())
