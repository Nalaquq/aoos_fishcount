"""Starlink / remote dashboard data push utilities."""

from __future__ import annotations

import json
import logging
from datetime import datetime

log = logging.getLogger(__name__)


def push_summary(
    summary: dict,
    endpoint: str | None = None,
    dry_run: bool = False,
) -> bool:
    """Push an hourly count summary to a remote endpoint.

    Args:
        summary: Dict containing species counts and health metrics.
        endpoint: HTTP POST endpoint URL. If None, logs locally only.
        dry_run: If True, print payload without sending.

    Returns:
        True if push succeeded (or dry_run), False on error.
    """
    payload = {
        "timestamp": datetime.now().isoformat(),
        "source": "aoos_fishcount",
        **summary,
    }

    if dry_run or endpoint is None:
        log.info("Push payload: %s", json.dumps(payload, indent=2))
        return True

    try:
        import requests
        resp = requests.post(endpoint, json=payload, timeout=30)
        resp.raise_for_status()
        log.info("Push succeeded: %s → HTTP %d", endpoint, resp.status_code)
        return True
    except Exception as exc:
        log.error("Push failed: %s", exc)
        return False
