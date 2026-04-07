"""Starlink / network connectivity monitoring."""

from __future__ import annotations

import logging
import subprocess

log = logging.getLogger(__name__)

# Cloudflare DNS — lightweight, reliable connectivity probe
_PING_TARGET = "1.1.1.1"
_PING_TIMEOUT = 5


def check_connectivity(target: str = _PING_TARGET, timeout: int = _PING_TIMEOUT) -> bool:
    """Return True if the host can reach *target* via ICMP ping."""
    try:
        result = subprocess.run(
            ["ping", "-c", "1", "-W", str(timeout), target],
            capture_output=True, timeout=timeout + 2,
        )
        return result.returncode == 0
    except Exception:
        return False


def check_tailscale() -> dict[str, bool | str | None]:
    """Return Tailscale daemon status and this node's IP.

    Returns:
        Dict with keys 'running' (bool) and 'ip' (str or None).
    """
    try:
        result = subprocess.run(
            ["tailscale", "status", "--json"],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode != 0:
            return {"running": False, "ip": None}

        import json
        status = json.loads(result.stdout)
        self_ip = None
        self_node = status.get("Self", {})
        addrs = self_node.get("TailscaleIPs", [])
        if addrs:
            self_ip = addrs[0]
        return {"running": True, "ip": self_ip}
    except FileNotFoundError:
        return {"running": False, "ip": None}
    except Exception as exc:
        log.debug("Tailscale status check failed: %s", exc)
        return {"running": False, "ip": None}
