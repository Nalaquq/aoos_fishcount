#!/usr/bin/env python3
"""Pre-deployment system health check.

Verifies: camera, Coral USB, BME280 sensor, Tailscale, disk space.

Usage:
    python scripts/health_check.py
"""

import subprocess
import sys
from pathlib import Path


def check(label: str, ok: bool, detail: str = "") -> bool:
    status = "  OK  " if ok else " FAIL "
    print(f"[{status}] {label}{': ' + detail if detail else ''}")
    return ok


def main():
    print("=" * 55)
    print("  aoos_fishcount — Pre-Deployment Health Check")
    print("=" * 55)
    results = []

    # Camera
    try:
        import cv2
        cap = cv2.VideoCapture(0)
        opened = cap.isOpened()
        cap.release()
        results.append(check("Camera /dev/video0", opened))
    except ImportError:
        results.append(check("Camera (OpenCV missing)", False))

    # Coral USB
    try:
        coral_path = Path("/dev/bus/usb")
        # Rough check — list USB devices and look for Google
        lsusb = subprocess.run(["lsusb"], capture_output=True, text=True)
        coral_found = "Google" in lsusb.stdout or "18d1" in lsusb.stdout
        results.append(check("Google Coral USB", coral_found))
    except Exception:
        results.append(check("Google Coral USB", False, "lsusb failed"))

    # BME280
    try:
        result = subprocess.run(
            ["i2cdetect", "-y", "1"], capture_output=True, text=True
        )
        bme = "76" in result.stdout or "77" in result.stdout
        results.append(check("BME280 (I2C)", bme, "addr 0x76 or 0x77"))
    except Exception:
        results.append(check("BME280 (I2C)", False, "i2cdetect not found"))

    # Network connectivity
    try:
        from aoos_fishcount.sensors.network import check_connectivity, check_tailscale
        results.append(check("Internet (ping)", check_connectivity()))
        ts_status = check_tailscale()
        results.append(check(
            "Tailscale", ts_status["running"],
            f"IP: {ts_status['ip']}" if ts_status["ip"] else "",
        ))
    except ImportError:
        try:
            ts = subprocess.run(
                ["tailscale", "status"], capture_output=True, text=True, timeout=5
            )
            results.append(check("Tailscale", ts.returncode == 0))
        except Exception:
            results.append(check("Tailscale", False, "not installed"))

    # Disk space (warn if < 2GB free on /)
    stat = Path("/").stat()
    import shutil
    free_gb = shutil.disk_usage("/").free / 1e9
    results.append(check("Disk space (/ free)", free_gb > 2.0, f"{free_gb:.1f} GB"))

    # Model file
    model_default = Path("data/models/salmon_yolov8n_edgetpu.tflite")
    results.append(check("Edge TPU model file", model_default.exists(), str(model_default)))

    print("=" * 55)
    if all(results):
        print("All checks passed — system ready for deployment.")
        return 0
    else:
        failed = sum(1 for r in results if not r)
        print(f"{failed} check(s) failed — review before deploying.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
