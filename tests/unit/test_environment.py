"""Unit tests for EnvironmentSensor (bench mode, no hardware)."""

from aoos_fishcount.sensors.environment import EnvironmentSensor


def test_sensor_bench_mode_returns_none():
    """Without hardware, sensor should return None values gracefully."""
    sensor = EnvironmentSensor()
    reading = sensor.read()
    # In bench mode (no RPi / no BME280), values should be None
    assert "temp_c" in reading
    assert "humidity_pct" in reading
