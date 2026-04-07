#!/usr/bin/env python3
"""Capture a frame and overlay the virtual counting line for on-site calibration.

Usage:
    python scripts/calibrate_line.py
    python scripts/calibrate_line.py --line-y 540 --output site_frame.jpg
    python scripts/calibrate_line.py --device 0 --line-y 400 --output calibration.jpg
"""

import argparse

import cv2
import numpy as np


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Capture a frame with counting line overlay for field calibration"
    )
    parser.add_argument("--device", type=int, default=0,
                        help="Video device index (default: 0)")
    parser.add_argument("--line-y", type=int, default=540,
                        help="Y pixel of the virtual counting line (default: 540)")
    parser.add_argument("--output", type=str, default="site_frame.jpg",
                        help="Output file path (default: site_frame.jpg)")
    parser.add_argument("--width", type=int, default=1920)
    parser.add_argument("--height", type=int, default=1080)
    args = parser.parse_args()

    cap = cv2.VideoCapture(args.device)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, args.width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, args.height)

    if not cap.isOpened():
        print(f"Cannot open camera device {args.device}")
        return 1

    # Grab a few frames to let auto-exposure settle
    for _ in range(10):
        cap.read()

    ret, frame = cap.read()
    cap.release()

    if not ret:
        print("Failed to capture frame")
        return 1

    # Draw the counting line in green
    cv2.line(frame, (0, args.line_y), (args.width, args.line_y), (0, 255, 0), 2)

    # Label the line
    label = f"LINE_Y = {args.line_y}"
    cv2.putText(
        frame, label, (10, args.line_y - 10),
        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2,
    )

    # Add upstream/downstream labels
    cv2.putText(
        frame, "UPSTREAM", (args.width - 200, args.line_y - 30),
        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1,
    )
    cv2.putText(
        frame, "DOWNSTREAM", (args.width - 230, args.line_y + 40),
        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 128, 255), 1,
    )

    cv2.imwrite(args.output, frame)
    print(f"Saved calibration frame: {args.output}")
    print(f"  LINE_Y = {args.line_y}")
    print(f"  Frame size = {args.width}x{args.height}")
    print(f"\nSCP to your laptop to review:")
    print(f"  scp pi@salmon-rpi:{args.output} .")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
