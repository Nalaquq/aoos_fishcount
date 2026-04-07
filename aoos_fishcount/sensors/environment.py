"""BME280 interior temperature and humidity sensor interface."""

from __future__ import annotations

import logging

log = logging.getLogger(__name__)


class EnvironmentSensor:
    """Reads temperature and humidity from a BME280 on I2C.

    Falls back gracefully if no sensor is detected (bench testing).
    """

    def __init__(self) -> None:
        self._sensor = None
        try:
            import board
            import busio
            import adafruit_bme280

            i2c = busio.I2C(board.SCL, board.SDA)
            self._sensor = adafruit_bme280.Adafruit_BME280_I2C(i2c)
            log.info("BME280 sensor detected")
        except Exception as exc:
            log.warning("BME280 not available (bench mode): %s", exc)

    def read(self) -> dict[str, float | None]:
        """Return current temperature and humidity.

        Returns:
            Dict with keys 'temp_c' and 'humidity_pct'.
            Values are None if sensor is unavailable.
        """
        if self._sensor is None:
            return {"temp_c": None, "humidity_pct": None}
        return {
            "temp_c": round(self._sensor.temperature, 1),
            "humidity_pct": round(self._sensor.relative_humidity, 1),
        }
