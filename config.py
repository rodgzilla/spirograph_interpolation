"""
Config - Configuration loading and validation module

This module handles loading spirograph configurations from JSON files,
validating them against a schema, and applying default values.
"""

import json
import re
from typing import Dict, Any, Union
from spirograph import calculate_required_rotations


class ConfigValidationError(Exception):
    """Exception raised when configuration validation fails"""
    pass


# JSON Schema for spirograph configuration
CONFIG_SCHEMA = {
    "type": "object",
    "required": ["wheels"],
    "properties": {
        "name": {"type": "string"},
        "wheels": {
            "type": "array",
            "minItems": 2,
            "maxItems": 2,
            "items": {"type": "object"}
        },
        "rotation_count": {
            "oneOf": [
                {"type": "integer", "minimum": 1},
                {"type": "string", "enum": ["auto"]}
            ]
        },
        "color": {"type": "string", "pattern": "^#[0-9A-Fa-f]{6}$"},
        "line_width": {"type": "number", "minimum": 0.1}
    }
}


# Default values for optional fields
DEFAULTS = {
    "name": "Spirograph",
    "color": "#2E86AB",
    "line_width": 2,
    "rotation_count": "auto"
}


def validate_wheels(wheels: list) -> None:
    """
    Validate wheel configurations.

    Supports 2+ wheels. For multi-wheel (3+), validates parent indices.

    Args:
        wheels: List of wheel dictionaries

    Raises:
        ConfigValidationError: If validation fails
    """
    if len(wheels) < 2:
        raise ConfigValidationError("Configuration must have at least 2 wheels")

    # Count fixed and moving wheels
    fixed_count = 0
    moving_count = 0
    has_pen = False

    for i, wheel in enumerate(wheels):
        if "type" not in wheel:
            raise ConfigValidationError(f"Wheel {i} must have a 'type' field")

        if wheel["type"] not in ["fixed", "moving"]:
            raise ConfigValidationError(f"Invalid wheel type: {wheel['type']}")

        if wheel["type"] == "fixed":
            fixed_count += 1
        else:
            moving_count += 1

        # Validate teeth
        if "teeth" not in wheel:
            raise ConfigValidationError(f"Wheel {i} missing 'teeth' field")

        teeth = wheel["teeth"]
        if not isinstance(teeth, (int, float)) or teeth <= 0:
            raise ConfigValidationError(f"Wheel {i}: teeth count must be positive, got {teeth}")

        # For multi-wheel configs (3+), validate parent_index
        if len(wheels) > 2 and i > 0:
            if "parent_index" not in wheel:
                # Default to previous wheel
                wheel["parent_index"] = i - 1
            else:
                parent_idx = wheel["parent_index"]
                if not isinstance(parent_idx, int) or parent_idx < 0 or parent_idx >= i:
                    raise ConfigValidationError(
                        f"Wheel {i}: parent_index must be a valid index < {i}, got {parent_idx}"
                    )

        # Check for pen_offset (at least one moving wheel should have it)
        if wheel["type"] == "moving" and "pen_offset" in wheel:
            pen_offset = wheel["pen_offset"]
            if not isinstance(pen_offset, (int, float)) or pen_offset < 0:
                raise ConfigValidationError(f"Wheel {i}: pen_offset must be non-negative, got {pen_offset}")
            has_pen = True

    # Validation rules
    if fixed_count == 0:
        raise ConfigValidationError("Configuration must have at least one 'fixed' wheel")

    if moving_count == 0:
        raise ConfigValidationError("Configuration must have at least one 'moving' wheel")

    # For 2-wheel configs, ensure backward compatibility
    if len(wheels) == 2:
        moving_wheel = next((w for w in wheels if w["type"] == "moving"), None)
        if "pen_offset" not in moving_wheel:
            raise ConfigValidationError("2-wheel config: moving wheel must have 'pen_offset' field")

    # For multi-wheel configs, at least the last wheel should have a pen
    if len(wheels) > 2:
        last_moving = next((w for w in reversed(wheels) if w["type"] == "moving"), None)
        if last_moving and "pen_offset" not in last_moving:
            # Add default pen_offset to last moving wheel
            last_moving["pen_offset"] = 0.7


def validate_color(color: str) -> None:
    """
    Validate hex color format.

    Args:
        color: Color string

    Raises:
        ConfigValidationError: If color format is invalid
    """
    pattern = re.compile(r'^#[0-9A-Fa-f]{6}$')
    if not pattern.match(color):
        raise ConfigValidationError(
            f"Color must be in hex format (#RRGGBB), got '{color}'"
        )


def load_config(file_path: str) -> Dict[str, Any]:
    """
    Load and validate a spirograph configuration from a JSON file.

    Args:
        file_path: Path to the JSON configuration file

    Returns:
        Validated configuration dictionary with defaults applied

    Raises:
        ConfigValidationError: If the configuration is invalid
        json.JSONDecodeError: If the JSON is malformed
    """
    # Load JSON file
    try:
        with open(file_path, 'r') as f:
            config = json.load(f)
    except json.JSONDecodeError as e:
        raise ConfigValidationError(f"Invalid JSON syntax: {e}")
    except FileNotFoundError:
        raise ConfigValidationError(f"Configuration file not found: {file_path}")

    # Apply defaults
    for key, default_value in DEFAULTS.items():
        if key not in config:
            config[key] = default_value

    # Validate wheels
    if "wheels" not in config:
        raise ConfigValidationError("Configuration must have 'wheels' field")

    validate_wheels(config["wheels"])

    # Validate color
    if "color" in config:
        validate_color(config["color"])

    # Validate line width
    if "line_width" in config:
        if not isinstance(config["line_width"], (int, float)) or config["line_width"] <= 0:
            raise ConfigValidationError(
                f"Line width must be positive, got {config['line_width']}"
            )

    # Handle auto rotation calculation
    if config["rotation_count"] == "auto":
        # Find fixed and moving teeth
        fixed_teeth = None
        moving_teeth = None

        for wheel in config["wheels"]:
            if wheel["type"] == "fixed":
                fixed_teeth = wheel["teeth"]
            elif wheel["type"] == "moving":
                moving_teeth = wheel["teeth"]

        if fixed_teeth and moving_teeth:
            config["rotation_count"] = calculate_required_rotations(
                fixed_teeth,
                moving_teeth
            )
        else:
            raise ConfigValidationError("Cannot auto-calculate rotations without teeth counts")
    else:
        # Validate manual rotation count
        if not isinstance(config["rotation_count"], int) or config["rotation_count"] < 1:
            raise ConfigValidationError(
                f"Rotation count must be a positive integer, got {config['rotation_count']}"
            )

    return config


def get_wheel_by_type(config: Dict[str, Any], wheel_type: str) -> Dict[str, Any]:
    """
    Get a wheel configuration by type.

    Args:
        config: Configuration dictionary
        wheel_type: Type of wheel ('fixed' or 'moving')

    Returns:
        Wheel configuration dictionary

    Raises:
        ValueError: If wheel of specified type is not found
    """
    for wheel in config["wheels"]:
        if wheel["type"] == wheel_type:
            return wheel

    raise ValueError(f"No wheel of type '{wheel_type}' found in configuration")
