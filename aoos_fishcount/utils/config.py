"""YAML configuration loader and validator."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


class ConfigError(Exception):
    """Raised when a config file is missing required keys."""


REQUIRED_KEYS: dict[str, list[str]] = {
    "site": ["name"],
    "camera": ["device_index", "width", "height", "fps"],
    "inference": ["model_path", "conf_threshold", "line_y"],
    "logging": ["db_path"],
}


def load_config(path: Path) -> dict[str, Any]:
    """Load and validate a deployment YAML config file.

    Args:
        path: Path to the YAML config file.

    Returns:
        Validated config dictionary with defaults merged in.

    Raises:
        ConfigError: If required keys are missing.
        FileNotFoundError: If the config file does not exist.
    """
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    with path.open() as f:
        cfg: dict[str, Any] = yaml.safe_load(f)

    _validate(cfg, path)
    return cfg


def _validate(cfg: dict[str, Any], path: Path) -> None:
    for section, keys in REQUIRED_KEYS.items():
        if section not in cfg:
            raise ConfigError(f"[{path}] Missing required section: '{section}'")
        for key in keys:
            if key not in cfg[section]:
                raise ConfigError(
                    f"[{path}] Missing required key: '{section}.{key}'"
                )
