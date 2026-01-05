"""
Configuration loader for the TR Text-Fabric pipeline.

Handles loading config.yaml with variable interpolation and path resolution.
"""

import os
import re
from pathlib import Path
from typing import Any

import yaml


# Default config file location
DEFAULT_CONFIG_PATH = Path(__file__).parent.parent.parent / "config.yaml"


def _interpolate_variables(config: dict, root: dict = None) -> dict:
    """
    Recursively interpolate ${var.path} references in config values.

    Args:
        config: The config dict to process
        root: The root config dict for variable lookup (defaults to config)

    Returns:
        Config dict with all variables interpolated
    """
    if root is None:
        root = config

    def resolve_reference(match: re.Match) -> str:
        """Resolve a ${var.path} reference."""
        path = match.group(1)
        parts = path.split(".")
        value = root
        for part in parts:
            if isinstance(value, dict) and part in value:
                value = value[part]
            else:
                raise ValueError(f"Cannot resolve config reference: ${{{path}}}")
        return str(value)

    def process_value(value: Any) -> Any:
        """Process a single value, interpolating if it's a string."""
        if isinstance(value, str):
            # Pattern matches ${paths.root} style references
            pattern = r"\$\{([^}]+)\}"
            # Keep interpolating until no more references
            prev_value = None
            while prev_value != value:
                prev_value = value
                value = re.sub(pattern, resolve_reference, value)
            return value
        elif isinstance(value, dict):
            return {k: process_value(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [process_value(v) for v in value]
        else:
            return value

    return process_value(config)


def load_config(config_path: Path = None) -> dict:
    """
    Load and parse the configuration file.

    Args:
        config_path: Path to config.yaml. Defaults to project root config.yaml

    Returns:
        Parsed configuration dictionary with interpolated variables

    Raises:
        FileNotFoundError: If config file doesn't exist
        yaml.YAMLError: If config file is invalid YAML
    """
    if config_path is None:
        config_path = DEFAULT_CONFIG_PATH

    config_path = Path(config_path).resolve()

    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    # Resolve "." in paths.root to config file's directory
    if config.get("paths", {}).get("root") == ".":
        config["paths"]["root"] = str(config_path.parent)

    # Interpolate variable references
    config = _interpolate_variables(config)

    return config


def get_path(config: dict, *keys: str) -> Path:
    """
    Get a path from the config, ensuring it exists.

    Args:
        config: The loaded config dict
        *keys: Path through the config dict (e.g., "paths", "data", "intermediate")

    Returns:
        Path object for the configured path

    Raises:
        KeyError: If the path doesn't exist in config
    """
    value = config
    for key in keys:
        if not isinstance(value, dict) or key not in value:
            raise KeyError(f"Config path not found: {'.'.join(keys)}")
        value = value[key]

    return Path(value)


def ensure_directories(config: dict) -> None:
    """
    Create all configured directories if they don't exist.

    Args:
        config: The loaded config dict
    """
    paths = config.get("paths", {})

    def create_paths(d: dict) -> None:
        for key, value in d.items():
            if isinstance(value, str) and "/" in value:
                path = Path(value)
                if not path.suffix:  # Only create directories, not files
                    path.mkdir(parents=True, exist_ok=True)
            elif isinstance(value, dict):
                create_paths(value)

    create_paths(paths)


if __name__ == "__main__":
    # Test config loading
    config = load_config()
    print("Config loaded successfully!")
    print(f"Project: {config['project']['name']}")
    print(f"Root path: {config['paths']['root']}")
    print(f"Data intermediate: {config['paths']['data']['intermediate']}")
