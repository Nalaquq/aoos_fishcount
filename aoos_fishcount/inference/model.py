"""YOLOv8 model wrapper supporting both CPU and Coral Edge TPU inference."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import numpy as np

log = logging.getLogger(__name__)


class SalmonDetector:
    """Wraps a YOLOv8 model for salmon detection.

    Supports:
    - Standard PyTorch (.pt) on CPU/GPU
    - Edge TPU INT8 TFLite (*_edgetpu.tflite) on Google Coral USB

    Args:
        model_path: Path to model weights file.
        conf_threshold: Minimum detection confidence (0–1).
    """

    def __init__(self, model_path: str | Path, conf_threshold: float = 0.45) -> None:
        self.model_path = Path(model_path)
        self.conf_threshold = conf_threshold
        self._model: Any = None
        self._load()

    def _load(self) -> None:
        if not self.model_path.exists():
            raise FileNotFoundError(f"Model weights not found: {self.model_path}")

        log.info("Loading model: %s", self.model_path)
        from ultralytics import YOLO
        self._model = YOLO(str(self.model_path), task="detect")
        log.info("Model loaded. Classes: %s", list(self._model.names.values()))

    def predict(self, frame: np.ndarray) -> Any:
        """Run inference on a single frame.

        Args:
            frame: BGR image array (H, W, 3).

        Returns:
            Ultralytics Results object.
        """
        return self._model(frame, conf=self.conf_threshold, verbose=False)[0]

    def track(self, frame: np.ndarray) -> Any:
        """Run inference + ByteTrack on a single frame.

        Args:
            frame: BGR image array (H, W, 3).

        Returns:
            Ultralytics Results object with tracking IDs assigned.
        """
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
