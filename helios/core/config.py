"""
Configuration management for HELIOS ETF FLOW.

Provides Pydantic settings for environment variables and
YAML configuration loaders for API sources, normalization,
and state definitions.
"""

import logging
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from helios.core.exceptions import ConfigurationError

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # API keys
    polygon_key: str = Field(..., validation_alias="POLYGON_KEY")
    fmp_key: str = Field(default="", validation_alias="FMP_KEY")
    uw_api_key: str = Field(default="", validation_alias="UW_API_KEY")

    # Paths
    data_dir: Path = Field(default=Path("data"))
    config_dir: Path = Field(default=Path("config"))

    # Logging
    log_level: str = Field(default="INFO")

    @property
    def raw_data_dir(self) -> Path:
        """Directory for raw API cache data."""
        path = self.data_dir / "raw"
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def processed_data_dir(self) -> Path:
        """Directory for processed output data."""
        path = self.data_dir / "processed"
        path.mkdir(parents=True, exist_ok=True)
        return path


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()  # type: ignore[call-arg]


def load_yaml_config(config_path: Path) -> dict[str, Any]:
    """
    Load a YAML configuration file.

    Args:
        config_path: Path to YAML file

    Returns:
        Parsed configuration dict

    Raises:
        ConfigurationError: If file not found or invalid YAML
    """
    if not config_path.exists():
        raise ConfigurationError(f"Config file not found: {config_path}")

    try:
        with open(config_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if data is None:
            return {}
        return dict(data)
    except yaml.YAMLError as e:
        raise ConfigurationError(f"Invalid YAML in {config_path}: {e}") from e


class SourcesConfig:
    """API source configuration loaded from settings.yaml."""

    def __init__(self, config_dir: Path | None = None) -> None:
        config_dir = config_dir or Path("config")
        self._data = load_yaml_config(config_dir / "settings.yaml")

    @property
    def polygon(self) -> dict[str, Any]:
        """Polygon API configuration."""
        return self._data.get("api_sources", {}).get("polygon", {})

    @property
    def fmp(self) -> dict[str, Any]:
        """FMP API configuration."""
        return self._data.get("api_sources", {}).get("fmp", {})

    @property
    def cache(self) -> dict[str, Any]:
        """Cache configuration."""
        return self._data.get("cache", {})


class NormalizationConfig:
    """Normalization configuration loaded from normalization.yaml."""

    def __init__(self, config_dir: Path | None = None) -> None:
        config_dir = config_dir or Path("config")
        self._data = load_yaml_config(config_dir / "normalization.yaml")

    @property
    def default_window(self) -> int:
        """Default rolling window size."""
        return self._data.get("normalization", {}).get("default_window", 63)

    @property
    def min_observations(self) -> int:
        """Minimum observations for valid baseline."""
        return self._data.get("normalization", {}).get("min_observations", 21)

    @property
    def features(self) -> dict[str, Any]:
        """Per-feature normalization config."""
        return self._data.get("normalization", {}).get("features", {})


class StatesConfig:
    """State configuration loaded from states.yaml."""

    def __init__(self, config_dir: Path | None = None) -> None:
        config_dir = config_dir or Path("config")
        self._data = load_yaml_config(config_dir / "states.yaml")

    @property
    def states(self) -> dict[str, Any]:
        """State definitions with thresholds and descriptions."""
        return self._data.get("states", {})

    @property
    def colors(self) -> dict[str, str]:
        """State display colors."""
        return self._data.get("display", {}).get("colors", {})
