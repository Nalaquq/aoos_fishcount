"""
Flask application for salmon species bounding box annotation.

Provides a web-based UI for labeling images with bounding boxes around
salmon species to generate YOLO-format training data.
"""

import argparse
import json
import os
import sys
import uuid
import webbrowser
from pathlib import Path
from threading import Timer

from flask import Flask, abort, jsonify, render_template, request, send_from_directory

from . import SPECIES_CLASSES, SPECIES_COLORS

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".webp"}


def create_app(input_dir: str, output_dir: str) -> Flask:
    """Create and configure the Flask labeling application."""
    input_path = Path(input_dir).resolve()
    output_path = Path(output_dir).resolve()

    if not input_path.is_dir():
        print(f"Error: input directory does not exist: {input_path}", file=sys.stderr)
        sys.exit(1)

    output_path.mkdir(parents=True, exist_ok=True)
    annotations_dir = output_path / "annotations"
    annotations_dir.mkdir(exist_ok=True)
    labels_dir = output_path / "labels"
    labels_dir.mkdir(exist_ok=True)

    app = Flask(__name__)
    app.config["INPUT_DIR"] = str(input_path)
    app.config["OUTPUT_DIR"] = str(output_path)
    app.config["ANNOTATIONS_DIR"] = str(annotations_dir)
    app.config["LABELS_DIR"] = str(labels_dir)

    def _list_images() -> list[str]:
        """Return sorted list of image filenames in input directory."""
        files = []
        for f in sorted(input_path.iterdir()):
            if f.suffix.lower() in IMAGE_EXTENSIONS and f.is_file():
                files.append(f.name)
        return files

    def _progress_path() -> Path:
        return output_path / "progress.json"

    def _load_progress() -> dict:
        p = _progress_path()
        if p.exists():
            return json.loads(p.read_text())
        return {"completed": [], "skipped": []}

    def _save_progress(progress: dict) -> None:
        _progress_path().write_text(json.dumps(progress, indent=2))

    def _annotation_path(filename: str) -> Path:
        stem = Path(filename).stem
        return annotations_dir / f"{stem}.json"

    def _label_path(filename: str) -> Path:
        stem = Path(filename).stem
        return labels_dir / f"{stem}.txt"

    def _load_annotations(filename: str) -> list[dict]:
        p = _annotation_path(filename)
        if p.exists():
            return json.loads(p.read_text())
        return []

    def _save_annotations(filename: str, annotations: list[dict]) -> None:
        _annotation_path(filename).write_text(json.dumps(annotations, indent=2))
        _export_yolo(filename, annotations)

    def _export_yolo(filename: str, annotations: list[dict]) -> None:
        """Write YOLO-format label file from annotations."""
        lines = []
        for ann in annotations:
            cls = ann["class_id"]
            x = ann["x"] + ann["w"] / 2
            y = ann["y"] + ann["h"] / 2
            lines.append(f"{cls} {x:.6f} {y:.6f} {ann['w']:.6f} {ann['h']:.6f}")
        _label_path(filename).write_text("\n".join(lines) + "\n" if lines else "")

    # --- Routes ---

    @app.route("/")
    def index():
        return render_template(
            "index.html",
            species_classes=SPECIES_CLASSES,
            species_colors=SPECIES_COLORS,
        )

    @app.route("/api/images")
    def api_images():
        images = _list_images()
        progress = _load_progress()
        return jsonify({
            "images": images,
            "total": len(images),
            "completed": progress.get("completed", []),
            "skipped": progress.get("skipped", []),
        })

    @app.route("/api/image/<path:filename>")
    def api_image(filename: str):
        if not (input_path / filename).is_file():
            abort(404)
        return send_from_directory(str(input_path), filename)

    @app.route("/api/annotations/<path:filename>", methods=["GET"])
    def api_get_annotations(filename: str):
        annotations = _load_annotations(filename)
        return jsonify({"filename": filename, "annotations": annotations})

    @app.route("/api/annotations/<path:filename>", methods=["POST"])
    def api_save_annotations(filename: str):
        data = request.get_json()
        annotations = data.get("annotations", [])
        for ann in annotations:
            if "id" not in ann:
                ann["id"] = str(uuid.uuid4())[:8]
        _save_annotations(filename, annotations)
        return jsonify({"status": "saved", "count": len(annotations)})

    @app.route("/api/annotations/<path:filename>/<box_id>", methods=["DELETE"])
    def api_delete_annotation(filename: str, box_id: str):
        annotations = _load_annotations(filename)
        annotations = [a for a in annotations if a.get("id") != box_id]
        _save_annotations(filename, annotations)
        return jsonify({"status": "deleted", "count": len(annotations)})

    @app.route("/api/progress", methods=["GET"])
    def api_get_progress():
        images = _list_images()
        progress = _load_progress()
        return jsonify({
            "total": len(images),
            "completed": len(progress.get("completed", [])),
            "skipped": len(progress.get("skipped", [])),
            "remaining": len(images)
            - len(progress.get("completed", []))
            - len(progress.get("skipped", [])),
        })

    @app.route("/api/progress/<path:filename>", methods=["POST"])
    def api_update_progress(filename: str):
        data = request.get_json()
        status = data.get("status")  # "completed" or "skipped"
        progress = _load_progress()
        for key in ("completed", "skipped"):
            if filename in progress.get(key, []):
                progress[key].remove(filename)
        if status in ("completed", "skipped"):
            progress.setdefault(status, []).append(filename)
        _save_progress(progress)
        return jsonify({"status": "updated"})

    @app.route("/api/export", methods=["POST"])
    def api_export():
        """Re-export all annotations to YOLO format."""
        images = _list_images()
        exported = 0
        for img in images:
            annotations = _load_annotations(img)
            if annotations:
                _export_yolo(img, annotations)
                exported += 1
        # Write classes.txt
        classes_path = output_path / "classes.txt"
        classes_path.write_text(
            "\n".join(SPECIES_CLASSES[i] for i in sorted(SPECIES_CLASSES)) + "\n"
        )
        # Write dataset.yaml for YOLO training
        yaml_path = output_path / "dataset.yaml"
        yaml_path.write_text(
            f"path: {output_path}\n"
            f"train: {input_path}\n"
            f"val: {input_path}\n\n"
            f"names:\n"
            + "".join(f"  {i}: {name}\n" for i, name in sorted(SPECIES_CLASSES.items()))
        )
        return jsonify({"status": "exported", "count": exported})

    return app


def main():
    """Entry point for the aoos-label console script."""
    parser = argparse.ArgumentParser(
        description="Salmon species labeling tool for YOLO training data",
        prog="aoos-label",
    )
    parser.add_argument(
        "--input", "-i",
        required=True,
        help="Path to directory containing images to label",
    )
    parser.add_argument(
        "--output", "-o",
        required=True,
        help="Path to output directory for annotations and YOLO labels",
    )
    parser.add_argument(
        "--port", "-p",
        type=int,
        default=5000,
        help="Port to run the labeling server on (default: 5000)",
    )
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Do not open a browser window automatically",
    )
    args = parser.parse_args()

    app = create_app(args.input, args.output)

    if not args.no_browser:
        Timer(1.0, lambda: webbrowser.open(f"http://localhost:{args.port}")).start()

    print(f"Labeling tool running at http://localhost:{args.port}")
    print(f"  Input:  {Path(args.input).resolve()}")
    print(f"  Output: {Path(args.output).resolve()}")
    print("Press Ctrl+C to stop.")

    app.run(host="127.0.0.1", port=args.port, debug=False)


if __name__ == "__main__":
    main()
