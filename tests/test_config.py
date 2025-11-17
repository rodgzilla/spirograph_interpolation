"""
Tests for config.py - Configuration loading and validation

Following TDD: Write tests first, then implement the functionality
"""
import pytest
import json
import tempfile
import os


def test_load_valid_json_config():
    """Test loading a valid JSON configuration file"""
    from config import load_config

    # Create a temporary JSON file
    config_data = {
        "name": "Test Spirograph",
        "wheels": [
            {"type": "fixed", "teeth": 96, "radius": 1.0},
            {"type": "moving", "teeth": 36, "radius": 0.375, "pen_offset": 0.7}
        ],
        "rotation_count": 3,
        "color": "#FF5733",
        "line_width": 2
    }

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(config_data, f)
        temp_path = f.name

    try:
        config = load_config(temp_path)
        assert config["name"] == "Test Spirograph"
        assert len(config["wheels"]) == 2
        assert config["wheels"][1]["teeth"] == 36
        assert config["color"] == "#FF5733"
    finally:
        os.unlink(temp_path)


def test_reject_invalid_schema():
    """Test that invalid configurations are rejected"""
    from config import load_config, ConfigValidationError

    # Missing required field (wheels)
    invalid_config = {
        "name": "Invalid",
        "color": "#FF5733"
    }

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(invalid_config, f)
        temp_path = f.name

    try:
        with pytest.raises(ConfigValidationError):
            load_config(temp_path)
    finally:
        os.unlink(temp_path)


def test_calculate_auto_rotations():
    """Test auto-calculation of rotation count from teeth"""
    from config import load_config

    config_data = {
        "name": "Auto Rotation Test",
        "wheels": [
            {"type": "fixed", "teeth": 96, "radius": 1.0},
            {"type": "moving", "teeth": 36, "radius": 0.375, "pen_offset": 0.7}
        ],
        "rotation_count": "auto",  # Should calculate automatically
        "color": "#FF5733",
        "line_width": 2
    }

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(config_data, f)
        temp_path = f.name

    try:
        config = load_config(temp_path)
        # Should calculate 36 / GCD(96, 36) = 36 / 12 = 3
        assert config["rotation_count"] == 3
    finally:
        os.unlink(temp_path)


def test_default_values():
    """Test that default values are applied correctly"""
    from config import load_config

    # Minimal config without optional fields
    config_data = {
        "name": "Minimal",
        "wheels": [
            {"type": "fixed", "teeth": 100},
            {"type": "moving", "teeth": 50, "pen_offset": 0.5}
        ]
    }

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(config_data, f)
        temp_path = f.name

    try:
        config = load_config(temp_path)
        # Should have default values
        assert "color" in config
        assert "line_width" in config
        assert "rotation_count" in config
    finally:
        os.unlink(temp_path)


def test_missing_required_fields():
    """Test error handling for missing required fields"""
    from config import load_config, ConfigValidationError

    # Missing pen_offset for moving wheel
    invalid_config = {
        "name": "Missing Field",
        "wheels": [
            {"type": "fixed", "teeth": 100},
            {"type": "moving", "teeth": 50}  # Missing pen_offset
        ]
    }

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(invalid_config, f)
        temp_path = f.name

    try:
        with pytest.raises(ConfigValidationError):
            load_config(temp_path)
    finally:
        os.unlink(temp_path)


def test_teeth_count_validation():
    """Test that teeth count must be positive"""
    from config import load_config, ConfigValidationError

    # Negative teeth count
    invalid_config = {
        "name": "Negative Teeth",
        "wheels": [
            {"type": "fixed", "teeth": -100},
            {"type": "moving", "teeth": 50, "pen_offset": 0.5}
        ]
    }

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(invalid_config, f)
        temp_path = f.name

    try:
        with pytest.raises(ConfigValidationError):
            load_config(temp_path)
    finally:
        os.unlink(temp_path)


def test_invalid_json_syntax():
    """Test handling of malformed JSON"""
    from config import load_config, ConfigValidationError

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write("{invalid json content")
        temp_path = f.name

    try:
        with pytest.raises((ConfigValidationError, json.JSONDecodeError)):
            load_config(temp_path)
    finally:
        os.unlink(temp_path)


def test_color_format_validation():
    """Test that color format is validated (hex codes)"""
    from config import load_config, ConfigValidationError

    # Invalid color format
    invalid_config = {
        "name": "Invalid Color",
        "wheels": [
            {"type": "fixed", "teeth": 100},
            {"type": "moving", "teeth": 50, "pen_offset": 0.5}
        ],
        "color": "not-a-hex-color"
    }

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(invalid_config, f)
        temp_path = f.name

    try:
        with pytest.raises(ConfigValidationError):
            load_config(temp_path)
    finally:
        os.unlink(temp_path)


# Tests for multi-wheel support
def test_3_wheel_config_validation():
    """Test that 3-wheel configurations are validated correctly"""
    from config import load_config

    config_data = {
        "name": "3-Wheel Test",
        "wheels": [
            {"type": "fixed", "teeth": 120, "radius": 1.0},
            {"type": "moving", "teeth": 60, "radius": 0.5, "parent_index": 0},
            {"type": "moving", "teeth": 30, "radius": 0.25, "parent_index": 1, "pen_offset": 0.8}
        ],
        "rotation_count": "auto"
    }

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(config_data, f)
        temp_path = f.name

    try:
        config = load_config(temp_path)
        assert len(config["wheels"]) == 3
        assert config["wheels"][1]["parent_index"] == 0
        assert config["wheels"][2]["parent_index"] == 1
    finally:
        os.unlink(temp_path)


def test_4_wheel_config_validation():
    """Test that 4-wheel configurations are validated correctly"""
    from config import load_config

    config_data = {
        "name": "4-Wheel Test",
        "wheels": [
            {"type": "fixed", "teeth": 160, "radius": 1.0},
            {"type": "moving", "teeth": 80, "radius": 0.5, "parent_index": 0},
            {"type": "moving", "teeth": 40, "radius": 0.25, "parent_index": 1},
            {"type": "moving", "teeth": 20, "radius": 0.125, "parent_index": 2, "pen_offset": 0.8}
        ],
        "rotation_count": "auto"
    }

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(config_data, f)
        temp_path = f.name

    try:
        config = load_config(temp_path)
        assert len(config["wheels"]) == 4
    finally:
        os.unlink(temp_path)


def test_multi_wheel_default_parent_index():
    """Test that parent_index defaults to previous wheel"""
    from config import load_config

    config_data = {
        "name": "Default Parent Test",
        "wheels": [
            {"type": "fixed", "teeth": 120, "radius": 1.0},
            {"type": "moving", "teeth": 60, "radius": 0.5},  # No parent_index
            {"type": "moving", "teeth": 30, "radius": 0.25, "pen_offset": 0.8}  # No parent_index
        ],
        "rotation_count": 5
    }

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(config_data, f)
        temp_path = f.name

    try:
        config = load_config(temp_path)
        # Should auto-assign parent_index
        assert config["wheels"][1]["parent_index"] == 0
        assert config["wheels"][2]["parent_index"] == 1
    finally:
        os.unlink(temp_path)


def test_multi_wheel_invalid_parent_index():
    """Test that invalid parent_index is rejected"""
    from config import load_config, ConfigValidationError

    # Parent index must be < current wheel index
    invalid_config = {
        "name": "Invalid Parent",
        "wheels": [
            {"type": "fixed", "teeth": 120, "radius": 1.0},
            {"type": "moving", "teeth": 60, "radius": 0.5, "parent_index": 0},
            {"type": "moving", "teeth": 30, "radius": 0.25, "parent_index": 5, "pen_offset": 0.8}  # Invalid: 5 >= 2
        ],
        "rotation_count": 5
    }

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(invalid_config, f)
        temp_path = f.name

    try:
        with pytest.raises(ConfigValidationError):
            load_config(temp_path)
    finally:
        os.unlink(temp_path)


def test_multi_wheel_default_pen_offset():
    """Test that pen_offset is auto-added to last moving wheel"""
    from config import load_config

    config_data = {
        "name": "Default Pen Test",
        "wheels": [
            {"type": "fixed", "teeth": 120, "radius": 1.0},
            {"type": "moving", "teeth": 60, "radius": 0.5, "parent_index": 0},
            {"type": "moving", "teeth": 30, "radius": 0.25, "parent_index": 1}  # No pen_offset
        ],
        "rotation_count": 5
    }

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(config_data, f)
        temp_path = f.name

    try:
        config = load_config(temp_path)
        # Should auto-add pen_offset to last moving wheel
        assert "pen_offset" in config["wheels"][2]
        assert config["wheels"][2]["pen_offset"] == 0.7
    finally:
        os.unlink(temp_path)


def test_multi_wheel_needs_at_least_one_fixed():
    """Test that multi-wheel configs must have at least one fixed wheel"""
    from config import load_config, ConfigValidationError

    invalid_config = {
        "name": "No Fixed Wheel",
        "wheels": [
            {"type": "moving", "teeth": 120, "radius": 1.0, "parent_index": 0},
            {"type": "moving", "teeth": 60, "radius": 0.5, "parent_index": 0},
            {"type": "moving", "teeth": 30, "radius": 0.25, "parent_index": 1, "pen_offset": 0.8}
        ],
        "rotation_count": 5
    }

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(invalid_config, f)
        temp_path = f.name

    try:
        with pytest.raises(ConfigValidationError):
            load_config(temp_path)
    finally:
        os.unlink(temp_path)


def test_multi_wheel_needs_at_least_one_moving():
    """Test that multi-wheel configs must have at least one moving wheel"""
    from config import load_config, ConfigValidationError

    invalid_config = {
        "name": "No Moving Wheel",
        "wheels": [
            {"type": "fixed", "teeth": 120, "radius": 1.0},
            {"type": "fixed", "teeth": 60, "radius": 0.5},
            {"type": "fixed", "teeth": 30, "radius": 0.25}
        ],
        "rotation_count": 5
    }

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(invalid_config, f)
        temp_path = f.name

    try:
        with pytest.raises(ConfigValidationError):
            load_config(temp_path)
    finally:
        os.unlink(temp_path)
