# Labeling Tool

A browser-based annotation tool for drawing bounding boxes around salmon species
in images. Generates YOLO-format training data for the YOLOv8 detection model.

## Installation

The labeling tool is included as an optional dependency of the main package:

```bash
pip install -e ".[labeling]"
```

This installs Flask and registers the `aoos-label` command.

## Usage

```bash
aoos-label --input /path/to/images --output /path/to/labels
```

This starts a local web server and opens the labeling UI in your default browser.

### Arguments

| Argument | Description |
|---|---|
| `--input`, `-i` | Directory containing images to label (required) |
| `--output`, `-o` | Directory for annotations and YOLO labels (required) |
| `--port`, `-p` | Port for the web server (default: 5000) |
| `--no-browser` | Don't open a browser automatically |

### Example

```bash
# Label images captured from the field camera
aoos-label -i data/captures/2026-06-15 -o data/training/2026-06-15
```

## Species Classes

| ID | Key | Species | Color |
|---|---|---|---|
| 0 | `1` | King (Chinook) | Red |
| 1 | `2` | Red (Sockeye) | Green |
| 2 | `3` | Silver (Coho) | Blue |
| 3 | `4` | Chum | Orange |
| 4 | `5` | Pink | Magenta |

## How to Label

1. **Select a species** — click a species button or press `1`-`5`.
2. **Draw a box** — click and drag on the image to draw a bounding box around a fish.
3. **Adjust a box** — click a box to select it, then drag its corner handles to resize
   or drag the box itself to move it.
4. **Change species** — select a box, then press `1`-`5` or click a species button to
   reclassify it.
5. **Delete a box** — select it and press `Delete`, or click the x button in the
   annotations list.
6. **Save** — press `Ctrl+S` or click Save. Annotations auto-save when navigating.
7. **Done & Next** — press `Enter` to mark the image as complete and advance.
8. **Skip** — press `S` to skip images with no fish or poor quality.

## Keyboard Shortcuts

| Key | Action |
|---|---|
| `1`-`5` | Select species |
| `Left` / `Right` | Navigate images |
| `Ctrl+S` | Save annotations |
| `Enter` | Mark done and go to next image |
| `S` | Skip image |
| `Delete` | Remove selected box |
| `Escape` | Cancel drawing / deselect |

## Output Structure

```
output/
├── annotations/        # JSON sidecar files (edit state)
│   ├── frame_001.json
│   └── frame_002.json
├── labels/             # YOLO-format label files
│   ├── frame_001.txt
│   └── frame_002.txt
├── classes.txt         # Species class names
├── dataset.yaml        # YOLO training config
└── progress.json       # Labeling progress tracker
```

### YOLO Label Format

Each `.txt` file contains one line per bounding box:

```
<class_id> <x_center> <y_center> <width> <height>
```

All coordinates are normalized to `[0, 1]` relative to image dimensions.

### Resuming Work

Progress is saved automatically. When you restart the tool pointing to the same
output directory, all previous annotations and progress are preserved.

## Export

Click **Export YOLO** to regenerate all YOLO label files, `classes.txt`, and
`dataset.yaml`. This is also done automatically each time you save, but the
export button is useful for batch re-export.

## Building a Standalone Executable

To create a standalone `.exe` that doesn't require a Python installation:

```bash
pip install pyinstaller
pyinstaller --onefile --add-data "aoos_fishcount/labeling/templates:templates" \
    --add-data "aoos_fishcount/labeling/static:static" \
    --name aoos-label \
    aoos_fishcount/labeling/app.py
```

The executable will be in `dist/aoos-label` (or `dist/aoos-label.exe` on Windows).
Users can run it from the command line with the same `--input` and `--output` arguments.
