"""YOLOv8 model wrapper supporting both CPU and Coral Edge TPU inference."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import cv2
import numpy as np

log = logging.getLogger(__name__)


def estimate_brightness(frame: np.ndarray) -> float:
    """Return mean brightness (0–255) of a frame via its V channel."""
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    return float(hsv[:, :, 2].mean())


class SalmonDetector:
    """Wraps a YOLOv8 model for salmon detection.

    Supports:
    - Standard PyTorch (.pt) on CPU/GPU
    - Edge TPU INT8 TFLite (*_edgetpu.tflite) on Google Coral USB

    Args:
        model_path: Path to model weights file.
        conf_threshold: Base detection confidence (0–1).
        adaptive_conf: If provided, dict with keys:
            bright_threshold (float): Confidence when brightness > bright_level (default 0.50).
            dim_threshold (float): Confidence when brightness < dim_level (default 0.35).
            bright_level (int): Brightness above which bright_threshold is used (default 140).
            dim_level (int): Brightness below which dim_threshold is used (default 60).
    """

    def __init__(
        self,
        model_path: str | Path,
        conf_threshold: float = 0.45,
        adaptive_conf: dict[str, float] | None = None,
    ) -> None:
        self.model_path = Path(model_path)
        self.base_conf = conf_threshold
        self.conf_threshold = conf_threshold
        self._adaptive = adaptive_conf
        self._model: Any = None
        self._load()

    def _load(self) -> None:
        if not self.model_path.exists():
            raise FileNotFoundError(f"Model weights not found: {self.model_path}")

        # Warn early if an Edge TPU model is loaded but no Coral device is found
        if "_edgetpu" in self.model_path.name:
            self._check_coral_device()

        log.info("Loading model: %s", self.model_path)
        from ultralytics import YOLO
        self._model = YOLO(str(self.model_path), task="detect")
        log.info("Model loaded. Classes: %s", list(self._model.names.values()))

    @staticmethod
    def _check_coral_device() -> None:
        """Log a warning if no Google Coral USB Accelerator is detected."""
        try:
            import subprocess
            result = subprocess.run(
                ["lsusb"], capture_output=True, text=True, timeout=5,
            )
            if "Google" not in result.stdout and "18d1" not in result.stdout:
                log.warning(
                    "Edge TPU model selected but no Google Coral USB detected. "
                    "Inference will fall back to CPU and be very slow. "
                    "Check: lsusb | grep -i google"
                )
        except Exception:
            pass  # lsusb not available (e.g. bench/dev machine)

    def adapt_confidence(self, frame: np.ndarray) -> None:
        """Adjust conf_threshold based on frame brightness.

        At dusk (low brightness), a lower threshold catches more fish.
        At midday (high brightness), a higher threshold reduces false
        positives from glare and debris.
        """
        if not self._adaptive:
            return

        brightness = estimate_brightness(frame)
        bright_level = self._adaptive.get("bright_level", 140)
        dim_level = self._adaptive.get("dim_level", 60)
        bright_thresh = self._adaptive.get("bright_threshold", 0.50)
        dim_thresh = self._adaptive.get("dim_threshold", 0.35)

        if brightness > bright_level:
            new_conf = bright_thresh
        elif brightness < dim_level:
            new_conf = dim_thresh
        else:
            # Linear interpolation between dim and bright
            ratio = (brightness - dim_level) / (bright_level - dim_level)
            new_conf = dim_thresh + ratio * (bright_thresh - dim_thresh)

        if abs(new_conf - self.conf_threshold) > 0.02:
            log.debug(
                "Adaptive conf: brightness=%.0f → conf=%.2f (was %.2f)",
                brightness, new_conf, self.conf_threshold,
            )
            self.conf_threshold = round(new_conf, 3)

    def predict(self, frame: np.ndarray) -> Any:
        """Run inference on a single frame.

        Args:
            frame: BGR image array (H, W, 3).

        Returns:
            Ultralytics Results object.
        """
        self.adapt_confidence(frame)
        return self._model(frame, conf=self.conf_threshold, verbose=False)[0]

    def track(self, frame: np.ndarray) -> Any:
        """Run inference + ByteTrack on a single frame.

        Args:
            frame: BGR image array (H, W, 3).

        Returns:
            Ultralytics Results object with tracking IDs assigned.
        """
        self.adapt_confidence(frame)
        return self._model.track(
            frame,
            persist=True,
            tracker="bytetrack.yaml",
            conf=self.conf_threshold,
            verbose=False,
        )[0]

    @property
    def class_names(self) -> dict[int, str]:
        return self._model.names
