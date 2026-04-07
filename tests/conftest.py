"""Shared pytest fixtures for aoos_fishcount tests."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import numpy as np
import pytest


@pytest.fixture
def sample_frame() -> np.ndarray:
    """Return a synthetic 1920x1080 BGR frame for testing."""
    return np.zeros((1080, 1920, 3), dtype=np.uint8)


@pytest.fixture
def sample_config() -> dict:
    """Return a minimal valid deployment config for testing."""
    return {
        "site": {"name": "Test Site", "latitude": 60.0, "longitude": -161.0},
        "camera": {"device_index": 0, "width": 1920, "height": 1080, "fps": 30},
        "inference": {
            "model_path": "data/models/test.tflite",
            "conf_threshold": 0.45,
            "line_y": 540,
        },
        "logging": {"db_path": "/tmp/test_fishcount.db"},
    }


@pytest.fixture
def tmp_db(tmp_path: Path):
    """Return a Database instance backed by a temp file."""
    from aoos_fishcount.utils.database import Database
    db = Database(tmp_path / "test.db")
    yield db
    db.close()


@pytest.fixture
def mock_camera():
    """Return a mock CameraCapture that yields synthetic frames."""
    cam = MagicMock()
    cam.read.return_value = np.zeros((1080, 1920, 3), dtype=np.uint8)
    return cam
