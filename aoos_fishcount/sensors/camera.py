"""Camera capture wrapper supporting both libcamera (RPi) and OpenCV."""

from __future__ import annotations

import logging
from typing import Any

import cv2
import numpy as np

log = logging.getLogger(__name__)


class CameraCapture:
    """Captures frames from the RPi HQ Camera via CSI-to-USB3 extender.

    Args:
        device_index: Video device index (0 = /dev/video0).
        width: Frame width in pixels.
        height: Frame height in pixels.
        fps: Target frame rate.
        exposure: Optional exposure config dict with keys:
            auto_exposure (int): OpenCV auto-exposure mode (3 = auto).
            exposure_value (int): Manual exposure bias (e.g. -6 for slight underexposure).
            white_balance_auto (bool): Lock white balance if False.
            red_balance (int): Manual red balance (e.g. 1400).
            blue_balance (int): Manual blue balance (e.g. 1600).
    """

    def __init__(
        self,
        device_index: int = 0,
        width: int = 1920,
        height: int = 1080,
        fps: int = 30,
        exposure: dict[str, Any] | None = None,
    ) -> None:
        self._cap = cv2.VideoCapture(device_index)
        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        self._cap.set(cv2.CAP_PROP_FPS, fps)

        if not self._cap.isOpened():
            raise RuntimeError(
                f"Cannot open camera device {device_index}. "
                "Check: ls /dev/video* and rpicam-hello --list-cameras"
            )

        if exposure:
            self._apply_exposure(exposure)

        log.info(
            "Camera opened: device=%d  %dx%d @ %dfps",
            device_index, width, height, fps,
        )

    def _apply_exposure(self, exposure: dict[str, Any]) -> None:
        """Apply exposure and white balance settings for field conditions.

        At 59°N latitude during salmon season, light changes dramatically
        between dawn, midday, and dusk.  Locking white balance and applying
        slight underexposure reduces glare blowout over water.
        """
        if "auto_exposure" in exposure:
            self._cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, exposure["auto_exposure"])
            log.info("Auto-exposure mode set to %d", exposure["auto_exposure"])

        if "exposure_value" in exposure:
            self._cap.set(cv2.CAP_PROP_EXPOSURE, exposure["exposure_value"])
            log.info("Exposure value set to %d", exposure["exposure_value"])

        if exposure.get("white_balance_auto") is False:
            self._cap.set(cv2.CAP_PROP_AUTO_WB, 0)
            if "red_balance" in exposure:
                self._cap.set(cv2.CAP_PROP_WB_TEMPERATURE, exposure["red_balance"])
            log.info("White balance locked (manual)")

    def read(self) -> np.ndarray | None:
        """Read and return a single frame, or None on failure."""
        ret, frame = self._cap.read()
        if not ret:
            log.warning("Frame read failed — check camera connection")
            return None
        return frame

    def release(self) -> None:
        """Release the camera resource."""
        self._cap.release()
        log.info("Camera released")
