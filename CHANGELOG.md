# Changelog

All notable changes to this project will be documented in this file.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

### Added
- Initial project scaffold
- YOLOv8 + ByteTrack single-camera inference pipeline
- BME280 interior environment monitoring
- SQLite count and health logging
- Starlink / Tailscale push integration
- PVC pole mount documentation
- Pelican 1120 camera head assembly guide
- DJI M300 electronics enclosure assembly guide
- Focus workflow with Laplacian sharpness monitor
- Field deployment and validation protocol docs

## [0.2.0] — 2026-04-07 — Build Guide Alignment

### Added
- **Exposure control** in `CameraCapture` — configurable auto-exposure, exposure bias,
  and locked white balance via `camera.exposure` config section. Reduces glare blowout
  over water at varying sun angles (build guide Section 7.4).
- **Adaptive confidence threshold** in `SalmonDetector` — automatically adjusts
  `conf_threshold` by frame brightness. Lower threshold at dusk catches more fish;
  higher at midday reduces false positives from glare/debris. Configurable via
  `inference.adaptive_conf` (build guide Section 7.4).
- **Bidirectional line crossing** in `LineCounter` — now detects both upstream and
  downstream crossings, with `net_upstream()` method. Reduces double-counting from
  milling fish that cross the line and fall back.
- **CPU temperature and undervoltage logging** in the pipeline health loop — calls
  `read_cpu_temp()` and `check_undervoltage()` from `power/monitor.py` every health
  interval. Warns if CPU > 80°C or undervoltage detected. CPU temp now written to
  the `health.cpu_temp_c` column (previously always NULL).
- **Disk space watchdog** in pipeline health loop — warns when free space drops
  below 2 GB. New `check_disk_space()` function in `power/monitor.py`.
- **Coral USB pre-check** on model load — if an `_edgetpu.tflite` model is selected
  but no Google Coral USB is detected via `lsusb`, logs a warning at startup instead
  of failing with a cryptic error.
- **Network connectivity monitor** — new `sensors/network.py` module with
  `check_connectivity()` (ICMP ping) and `check_tailscale()` (daemon status + IP).
  Integrated into `scripts/health_check.py`.
- **LINE_Y calibration tool** — new `scripts/calibrate_line.py` captures a frame with
  the virtual counting line overlaid in green, with upstream/downstream labels, for
  on-site setup (build guide Section 9.2).
- **Validation / accuracy script** — new `scripts/validate_counts.py` compares CV
  counts against observer CSV tallies and reports detection efficiency, species
  classification accuracy, false positive rate, and system uptime. Outputs the
  scientifically defensible reporting format required by KRITFC/ADF&G (build guide
  Section 10).
- **`build_guide/` directory** for storing physical build documentation — PDF build
  guide, parts list spreadsheets, wiring diagrams, and reference documents. Named
  `build_guide/` (not `build/`) to avoid conflict with the Python `build/` gitignore
  rule. Moved `Salmon CV System Build Guide.pdf` and `ROP.SF.3F.2019.03.pdf` from
  repo root into this directory.
- New unit tests for downstream crossing, `net_upstream()`, health data in push
  payload, and CPU temp in health logging.

### Changed
- **`hourly_summary()` return format** — now returns `{"counts": {...},
  "interior_temp_c": ..., "interior_rh_pct": ..., "cpu_temp_c": ...}` instead of
  a flat species-count dict. Push payloads now include enclosure health data so
  remote operators can monitor conditions via Starlink.
- **`LineCounter.update()` return type** — changed from `bool` to
  `str | None` (`"upstream"`, `"downstream"`, or `None`).
- `default.yaml` and `deployment_template.yaml` updated with `camera.exposure` and
  `inference.adaptive_conf` config sections.
- `README.md` updated with new project structure (`build_guide/`, `network.py`,
  `calibrate_line.py`, `validate_counts.py`), exposure/adaptive-conf config examples,
  validation script usage, and build guide section.
- `.gitignore` updated with `!build_guide/` exception so physical build docs are
  tracked in git (the existing `build/` rule is for Python packaging output).
