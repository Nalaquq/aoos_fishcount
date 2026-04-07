#!/usr/bin/env python3
"""Manually trigger an hourly count summary push.

Usage:
    python scripts/push_summary.py --config config/my_site.yaml
    python scripts/push_summary.py --config config/my_site.yaml --dry-run
"""
import argparse
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Push hourly count summary")
    parser.add_argument("--config", type=Path, default=Path("config/default.yaml"))
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    from aoos_fishcount.utils.config import load_config
    from aoos_fishcount.utils.database import Database
    from aoos_fishcount.utils.push import push_summary

    cfg = load_config(args.config)
    db = Database(cfg["logging"]["db_path"])
    summary = db.hourly_summary()
    db.close()

    endpoint = cfg.get("push", {}).get("endpoint")
    ok = push_summary(summary, endpoint=endpoint, dry_run=args.dry_run)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
