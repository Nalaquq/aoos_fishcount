"""System power, CPU health, and disk space monitoring."""

from __future__ import annotations

import logging
import shutil
from pathlib import Path

log = logging.getLogger(__name__)


def read_cpu_temp() -> float | None:
    """Read RPi CPU temperature from the thermal zone file.

    Returns:
        CPU temperature in Celsius, or None if not available.
    """
    thermal_path = Path("/sys/class/thermal/thermal_zone0/temp")
    if not thermal_path.exists():
        return None
    try:
        return round(int(thermal_path.read_text().strip()) / 1000, 1)
    except (OSError, ValueError):
        return None


def check_undervoltage() -> bool:
    """Check if the RPi is reporting an undervoltage condition.

    Returns:
        True if undervoltage has been detected.
    """
    vcgencmd_path = Path("/usr/bin/vcgencmd")
    if not vcgencmd_path.exists():
        return False
    try:
        import subprocess
        result = subprocess.run(
            [str(vcgencmd_path), "get_throttled"],
            capture_output=True, text=True, timeout=5,
        )
        throttled = int(result.stdout.strip().split("=")[1], 16)
        return bool(throttled & 0x1)  # bit 0 = undervoltage detected
    except Exception:
        return False


def check_disk_space(path: str = "/", min_gb: float = 2.0) -> tuple[float, bool]:
    """Check free disk space on the filesystem containing *path*.

    Args:
        path: Any path on the target filesystem (default: root).
        min_gb: Minimum acceptable free space in GB.

    Returns:
        Tuple of (free_gb, is_ok).
    """
    usage = shutil.disk_usage(path)
    free_gb = round(usage.free / 1e9, 2)
    return free_gb, free_gb >= min_gb
