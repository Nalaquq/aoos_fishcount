"""Camera capture wrapper supporting both libcamera (RPi) and OpenCV."""

from __future__ import annotations

import logging

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
    """

    def __init__(
        self,
        device_index: int = 0,
        width: int = 1920,
        height: int = 1080,
        fps: int = 30,
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
        log.info(
            "Camera opened: device=%d  %dx%d @ %dfps",
            device_index, width, height, fps,
        )

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
