#!/usr/bin/env python3
"""Real-time lens sharpness monitor for bench focus calibration.

Usage:
    python scripts/focus_check.py
    python scripts/focus_check.py --device 0 --save focus_frame.jpg
"""

import argparse
import time
import cv2
import numpy as np


def laplacian_sharpness(frame: np.ndarray) -> float:
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    return cv2.Laplacian(gray, cv2.CV_64F).var()


def main():
    parser = argparse.ArgumentParser(description="Live lens sharpness monitor")
    parser.add_argument("--device", type=int, default=0)
    parser.add_argument("--save", type=str, default=None,
                        help="Save a frame to this path when sharpness peaks")
    args = parser.parse_args()

    cap = cv2.VideoCapture(args.device)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)

    if not cap.isOpened():
        print(f"Cannot open camera device {args.device}")
        return 1

    print("Focus check running — rotate the lens focus ring.")
    print("Higher sharpness = better focus. Press Ctrl+C to stop.\n")

    peak = 0.0
    peak_frame = None

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                continue
            sharpness = laplacian_sharpness(frame)
            if sharpness > peak:
                peak = sharpness
                peak_frame = frame.copy()
            print(f"\rSharpness: {sharpness:8.1f}   Peak: {peak:8.1f}", end="", flush=True)
            time.sleep(0.2)
    except KeyboardInterrupt:
        print(f"\n\nFinal peak sharpness: {peak:.1f}")
        if args.save and peak_frame is not None:
            cv2.imwrite(args.save, peak_frame)
            print(f"Peak frame saved to: {args.save}")
    finally:
        cap.release()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
