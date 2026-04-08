# aoos_fishcount

**Field-deployable salmon escapement counting system for Kuskokwim Basin tributaries.**

Developed by [Nalaquq, LLC](https://nalaquq.com) (Quinhagak, Alaska) 
and funded under an Alaska Ocean Observation System (AOOS) grant.

---

## Overview

This system uses a Raspberry Pi 5 with a Google Coral USB accelerator to run a YOLOv8
object detection model and ByteTrack multi-object tracker on a 12.3MP color camera mounted
at an oblique angle over salmon-bearing rivers. Fish crossing a virtual counting line are
counted, species-classified, and logged to a local SQLite database. Count summaries are
pushed to a remote dashboard via Starlink Mini and Tailscale.

### System at a Glance

```
Camera (RPi HQ IMX477, 8mm CS lens, circular polarizer)
    ↓  CSI-to-USB3 extender (5m)
RPi 5 (8GB) + Google Coral USB
    ↓  YOLOv8n (Edge TPU INT8) + ByteTrack
SQLite count log  →  Starlink Mini  →  Remote dashboard
```

### Design Rationale

- **Single color camera** — at 59°N, civil twilight lasts all night during peak salmon
  season (May–August). A standard color camera with IR filter intact provides accurate
  species color data across nearly all deployment hours without artificial illumination.
- **IR illumination excluded** — 850nm IR does not penetrate water at fish swimming
  depth. Visible spotlights alter salmon migration behavior and increase predation risk.
- **PVC pole mount** — lower cost, locally repairable, height-adjustable, and transport-
  friendly for remote Kuskokwim tributary sites accessed by skiff or ATV.

---

## Hardware Requirements

| Component | Specification |
|---|---|
| Compute | Raspberry Pi 5 (8GB RAM) |
| AI Accelerator | Google Coral USB Accelerator |
| Camera | RPi HQ Camera (IMX477, 12.3MP), IR filter intact |
| Lens | Arducam 8mm CS-mount, F/1.2 |
| Polarizer | 40.5mm circular polarizing filter (slim CPL) |
| Camera head | Pelican 1120 NF case |
| Electronics enclosure | DJI M300 transport case |
| Power | 12V battery (Yeti 500X or 100Ah AGM) + 100W solar |
| Connectivity | Starlink Mini + Tailscale |

See [docs/hardware/](docs/hardware/) for full assembly guides.

---

## Quick Start

### Prerequisites

- Raspberry Pi 5 with Raspberry Pi OS (64-bit Bookworm)
- Google Coral USB Accelerator
- Python 3.11+

### Installation

```bash
# Clone the repository
git clone https://github.com/Nalaquq/aoos_fishcount.git
cd aoos_fishcount

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install the package
pip install -e ".[dev]"

# Install Coral Edge TPU runtime (RPi only)
bash scripts/install_coral.sh

# Copy and edit your deployment config
cp config/deployment_template.yaml config/my_site.yaml
# Edit config/my_site.yaml for your deployment
```

### Running the Pipeline

```bash
# Verify camera, sensors, Coral, network, and disk space
python scripts/health_check.py

# Focus check at 12-foot working distance
python scripts/focus_check.py

# Capture a frame with counting line overlay for on-site calibration
python scripts/calibrate_line.py --line-y 540 --output site_frame.jpg

# Start the counting pipeline
python -m aoos_fishcount --config config/my_site.yaml
```

### Running as Systemd Services (Field Deployment)

```bash
# Deploy systemd services for auto-start on boot
bash scripts/deploy.sh
sudo systemctl status aoos-fishcount
```

---

## Project Structure

```
aoos_fishcount/
├── aoos_fishcount/          # Main Python package
│   ├── inference/           # Detection, tracking, counting
│   │   ├── pipeline.py      # Main inference loop
│   │   ├── model.py         # YOLOv8 / Coral TPU model wrapper
│   │   │                    #   + adaptive confidence by brightness
│   │   ├── tracker.py       # ByteTrack multi-object tracker
│   │   └── counter.py       # Virtual line crossing counter (bidirectional)
│   ├── sensors/             # Hardware interfaces
│   │   ├── camera.py        # Camera capture + exposure control
│   │   ├── environment.py   # BME280 temp/humidity sensor
│   │   └── network.py       # Starlink / Tailscale connectivity monitor
│   ├── power/               # Power monitoring
│   │   └── monitor.py       # CPU temp, undervoltage, disk space
│   └── utils/               # Shared utilities
│       ├── config.py        # YAML config loader and validator
│       ├── database.py      # SQLite count and health logging
│       ├── logging.py       # Structured logging setup
│       └── push.py          # Starlink / remote data push
├── build_guide/             # Physical build documentation
│   │                        #   PDFs, parts lists, wiring diagrams
│   ├── Salmon CV System Build Guide.pdf
│   └── ...                  # Spreadsheets, vendor quotes, etc.
├── docs/                    # Software & field documentation
│   ├── hardware/            # Physical assembly guides
│   ├── software/            # Software setup guides
│   └── field/               # Field deployment protocols
├── tests/                   # Test suite
│   ├── unit/                # Unit tests (no hardware required)
│   ├── integration/         # Integration tests (hardware required)
│   └── fixtures/            # Test data and mock frames
├── scripts/                 # Standalone utility scripts
│   ├── deploy.sh            # Install systemd services
│   ├── install_coral.sh     # Coral Edge TPU runtime installer
│   ├── focus_check.py       # Real-time lens sharpness monitor
│   ├── calibrate_line.py    # Capture frame with LINE_Y overlay
│   ├── validate_counts.py   # Compare CV vs observer counts
│   ├── export_model.py      # Export YOLOv8 to Edge TPU TFLite
│   ├── push_summary.py      # Manual hourly summary push
│   └── health_check.py      # Pre-deployment system check
├── config/                  # Configuration files
│   ├── default.yaml         # Default configuration values
│   └── deployment_template.yaml  # Template for new sites
├── data/                    # Runtime data (gitignored)
│   ├── models/              # Edge TPU .tflite model files
│   ├── logs/                # Application logs
│   └── counts/              # SQLite databases
│
│   # Labeling subpackage (inside aoos_fishcount/)
│   labeling/
│   ├── app.py               # Flask labeling web app
│   ├── static/              # JS + CSS for canvas UI
│   └── templates/           # HTML template
```

---

## Labeling Tool

A browser-based annotation tool for creating YOLO training data. Designed for
non-expert users (e.g., Yup'ik employees who can identify salmon species) to draw
bounding boxes around fish in images captured by the field camera.

### Installation

```bash
# Install with labeling dependencies (adds Flask)
pip install -e ".[labeling]"
```

### Usage

```bash
# Point at a folder of images and an output folder for labels
aoos-label --input data/captures/2026-06-15 --output data/training/2026-06-15
```

This opens a web UI in your default browser. Draw bounding boxes, select species
(king, red, silver, chum, pink), and save. Progress is preserved across sessions —
restarting the tool with the same output directory picks up where you left off.

Output includes YOLO-format `.txt` label files, `classes.txt`, and `dataset.yaml`
ready for YOLOv8 training. See [docs/software/labeling.md](docs/software/labeling.md)
for the full user guide, keyboard shortcuts, and instructions for building a
standalone `.exe` with PyInstaller.

---

## Configuration

All deployment parameters are controlled via YAML config. Copy the template and edit for
your site:

```bash
cp config/deployment_template.yaml config/my_site.yaml
```

Key parameters:

```yaml
site:
  name: "Kwethluk River — Mile 12"
  river_width_m: 3.2
  latitude: 60.123
  longitude: -161.456

camera:
  device_index: 0
  width: 1920
  height: 1080
  fps: 30
  exposure:                    # Glare reduction for oblique water views
    auto_exposure: 3           # 3 = auto mode
    exposure_value: -6         # Slight underexposure reduces glare blowout
    white_balance_auto: false  # Lock WB to prevent flicker at dusk
    red_balance: 1400
    blue_balance: 1600

inference:
  model_path: "data/models/salmon_yolov8n_edgetpu.tflite"
  conf_threshold: 0.45
  line_y: 540                  # Virtual counting line, Y pixels from top
  adaptive_conf:               # Auto-adjust threshold by ambient light
    bright_threshold: 0.50     # Midday — higher to reduce FP from glare
    dim_threshold: 0.35        # Dusk/dawn — lower to catch more fish
    bright_level: 140
    dim_level: 60

logging:
  db_path: "data/counts/fishcount.db"
  push_interval_minutes: 60
```

---

## Model

Pre-trained weights are available from the
[Salmon Computer Vision project](https://github.com/Salmon-Computer-Vision/salmon-computer-vision).
Export to Edge TPU format for the Coral accelerator:

```bash
python scripts/export_model.py --weights salmon_yolov8n.pt --output data/models/
```

---

## Validation

Detection efficiency must be established through concurrent observer counts before
deploying unattended. See [docs/field/validation_protocol.md](docs/field/validation_protocol.md)
and the [Salmon CV System Build Guide](build_guide/) Section 10.

After collecting observer tallies in CSV format, run the validation script:

```bash
python scripts/validate_counts.py --db data/counts/fishcount.db --observer observer_tallies.csv
```

This reports detection efficiency, species classification accuracy, false positive rate,
and system uptime, along with the scientifically defensible reporting format required by
KRITFC/ADF&G for incorporation into escapement models.

Target metrics:
- Detection efficiency: > 0.80
- Species classification accuracy: > 0.85 (sockeye, coho)
- False positive rate: < 0.05
- System uptime: > 0.95

---

## Build Guide

The `build_guide/` directory contains the physical build documentation for the complete
field-deployable system, including:

- **Salmon CV System Build Guide** (PDF) — 33-page document covering system architecture,
  complete parts list (~$1,025 BOM), 6-phase assembly, software stack setup, focus
  workflow, field deployment protocol, and troubleshooting.
- Parts list spreadsheets, wiring diagrams, and vendor reference documents.

This is the authoritative reference for the hardware side of the project. The software in
this repository implements the pipeline described in the guide's Phase 4 (Software Stack).

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). This project follows the
[KRITFC open-source data principles](https://www.kuskosalmon.org/alternative-assessment-studies)
and is intended to support Tribal capacity building in fisheries monitoring technology.

---

## License

MIT License — see [LICENSE](LICENSE).

---

## Acknowledgments
