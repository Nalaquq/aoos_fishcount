"""Camera capture wrapper using Picamera2 for RPi5."""

from __future__ import annotations

import logging
from typing import Any

import numpy as np
from picamera2 import Picamera2

log = logging.getLogger(__name__)


class Picamera2Capture:
    """Captures frames from the RPi camera using Picamera2 library.

    Designed for RPi5 with HQ Camera module.

    Args:
        device_index: Camera index (0 = primary camera). Note: Picamera2 doesn't use device_index like OpenCV.
        width: Frame width in pixels.
        height: Frame height in pixels.
        fps: Target frame rate.
        exposure: Optional exposure config dict with keys:
            auto_exposure (bool): Enable auto exposure (default True).
            exposure_time (int): Manual exposure time in microseconds.
            analog_gain (float): Analog gain multiplier (default 1.0).
            digital_gain (float): Digital gain multiplier (default 1.0).
            awb_mode (str): Auto white balance mode ('auto', 'tungsten', 'daylight', 'cloudy', etc).
            color_gains (tuple): Manual (r_gain, b_gain) when awb_mode is manual.
    """

    def __init__(
        self,
        device_index: int = 0,
        width: int = 1920,
        height: int = 1080,
        fps: int = 30,
        exposure: dict[str, Any] | None = None,
    ) -> None:
        self.device_index = device_index
        self.width = width
        self.height = height
        self.fps = fps

        try:
            self.picam2 = Picamera2(camera_num=device_index)
        except Exception as e:
            raise RuntimeError(
                f"Cannot initialize Picamera2 device {device_index}. "
                f"Ensure RPi5 is running with Picamera2 installed. Error: {e}"
            )

        # Configure camera
        config = self.picam2.create_preview_configuration(
            main={"size": (width, height), "format": "BGR888"}
        )
        self.picam2.configure(config)

        # Apply exposure settings if provided
        if exposure:
            self._apply_exposure(exposure)

        # Start camera
        self.picam2.start()

        log.info(
            "Picamera2 initialized: device=%d  %dx%d @ %dfps",
            device_index,
            width,
            height,
            fps,
        )

    def _apply_exposure(self, exposure: dict[str, Any]) -> None:
        """Apply exposure and color settings for field conditions.

        At 59°N latitude during salmon season, light changes dramatically
        between dawn, midday, and dusk. Manual exposure control reduces
        glare blowout over water.
        """
        try:
            controls = {}

            # Auto exposure control
            if "auto_exposure" in exposure:
                auto_exp = exposure["auto_exposure"]
                if isinstance(auto_exp, bool):
                    controls["AeEnable"] = auto_exp
                else:
                    controls["AeEnable"] = bool(auto_exp)
                log.info("Auto-exposure: %s", controls["AeEnable"])

            # Manual exposure time (microseconds)
            if "exposure_time" in exposure and not exposure.get("auto_exposure", True):
                controls["ExposureTime"] = exposure["exposure_time"]
                log.info("Exposure time set to %d µs", exposure["exposure_time"])

            # Analog gain
            if "analog_gain" in exposure:
                controls["AnalogueGain"] = exposure["analog_gain"]
                log.info("Analog gain set to %.2f", exposure["analog_gain"])

            # Digital gain
            if "digital_gain" in exposure:
                controls["DigitalGain"] = exposure["digital_gain"]
                log.info("Digital gain set to %.2f", exposure["digital_gain"])

            # Auto white balance mode
            if "awb_mode" in exposure:
                awb_mode = exposure["awb_mode"]
                awb_modes = {
                    "auto": 0,
                    "tungsten": 1,
                    "daylight": 2,
                    "cloudy": 3,
                    "manual": 4,
                }
                if awb_mode in awb_modes:
                    controls["AwbMode"] = awb_modes[awb_mode]
                    log.info("AWB mode set to %s", awb_mode)

            # Manual color gains (only when awb_mode is manual)
            if "color_gains" in exposure:
                gains = exposure["color_gains"]
                controls["ColourGains"] = gains
                log.info("Color gains set to R=%.2f, B=%.2f", gains[0], gains[1])

            # Apply all controls
            if controls:
                self.picam2.set_controls(controls)
                log.info("Applied exposure controls: %s", controls)

        except Exception as e:
            log.error("Failed to apply exposure settings: %s", e)

    def read(self) -> np.ndarray | None:
        """Read and return a single frame, or None on failure."""
        try:
            array = self.picam2.capture_array()
            if array is None:
                log.warning("Frame capture returned None")
                return None
            return array
        except Exception as e:
            log.warning("Frame read failed: %s", e)
            return None

    def release(self) -> None:
        """Release the camera resource."""
        try:
            self.picam2.stop()
            log.info("Picamera2 stopped")
        except Exception as e:
            log.error("Error stopping Picamera2: %s", e)
