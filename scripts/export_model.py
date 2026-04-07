#!/usr/bin/env python3
"""Export YOLOv8 weights to Edge TPU TFLite format for Google Coral.

Run this on an x86 machine (more RAM than RPi for export).

Usage:
    python scripts/export_model.py --weights salmon_yolov8n.pt
    python scripts/export_model.py --weights salmon_yolov8n.pt --output data/models/
"""

import argparse
import shutil
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Export YOLOv8 → Edge TPU TFLite")
    parser.add_argument("--weights", type=Path, required=True,
                        help="Path to YOLOv8 .pt weights file")
    parser.add_argument("--output", type=Path, default=Path("data/models/"),
                        help="Output directory (default: data/models/)")
    parser.add_argument("--imgsz", type=int, default=640,
                        help="Inference image size (default: 640)")
    args = parser.parse_args()

    if not args.weights.exists():
        print(f"Weights file not found: {args.weights}")
        return 1

    args.output.mkdir(parents=True, exist_ok=True)

    print(f"Exporting: {args.weights} → Edge TPU TFLite")
    print("This may take several minutes...")

    from ultralytics import YOLO
    model = YOLO(str(args.weights))
    model.export(format="edgetpu", imgsz=args.imgsz)

    # YOLOv8 export places the file next to the weights
    exported = args.weights.parent / (args.weights.stem + "_edgetpu.tflite")
    if exported.exists():
        dest = args.output / exported.name
        shutil.move(str(exported), str(dest))
        print(f"Saved: {dest}")
        print(f"\nCopy to RPi:  scp {dest} pi@salmon-rpi:~/salmon_cv/{dest}")
    else:
        print(f"Export complete. Look for *_edgetpu.tflite near {args.weights}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
