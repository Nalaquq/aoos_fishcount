"""Entry point for `python -m aoos_fishcount`."""

import argparse
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Salmon escapement counting system — Nalaquq LLC / KRITFC"
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("config/default.yaml"),
        help="Path to deployment YAML config (default: config/default.yaml)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Initialize pipeline but do not start inference loop",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s 0.1.0",
    )
    args = parser.parse_args()

    if not args.config.exists():
        print(f"Config file not found: {args.config}", file=sys.stderr)
        print("Copy config/deployment_template.yaml to get started.", file=sys.stderr)
        return 1

    from aoos_fishcount.utils.config import load_config
    from aoos_fishcount.inference.pipeline import Pipeline

    cfg = load_config(args.config)
    pipeline = Pipeline(cfg)

    if args.dry_run:
        print("Dry run complete — pipeline initialized successfully.")
        return 0

    pipeline.run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
