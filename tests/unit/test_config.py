"""Unit tests for config loader."""

from pathlib import Path
import pytest
import yaml

from aoos_fishcount.utils.config import load_config, ConfigError


def test_load_valid_config(tmp_path, sample_config):
    cfg_path = tmp_path / "test.yaml"
    cfg_path.write_text(yaml.dump(sample_config))
    loaded = load_config(cfg_path)
    assert loaded["site"]["name"] == "Test Site"
    assert loaded["inference"]["line_y"] == 540


def test_missing_file_raises():
    with pytest.raises(FileNotFoundError):
        load_config(Path("/nonexistent/path.yaml"))


def test_missing_section_raises(tmp_path, sample_config):
    del sample_config["inference"]
    cfg_path = tmp_path / "bad.yaml"
    cfg_path.write_text(yaml.dump(sample_config))
    with pytest.raises(ConfigError, match="inference"):
        load_config(cfg_path)


def test_missing_key_raises(tmp_path, sample_config):
    del sample_config["camera"]["fps"]
    cfg_path = tmp_path / "bad.yaml"
    cfg_path.write_text(yaml.dump(sample_config))
    with pytest.raises(ConfigError, match="fps"):
        load_config(cfg_path)
