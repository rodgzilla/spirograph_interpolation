"""
Tests for interpolator.py - Interpolation and easing functions

Following TDD: Write tests first, then implement the functionality
"""
import pytest


# Easing function tests
def test_linear_easing():
    """Test linear easing function (f(t) = t)"""
    from interpolator import linear

    assert linear(0.0) == 0.0
    assert linear(0.5) == 0.5
    assert linear(1.0) == 1.0
    assert linear(0.25) == 0.25


def test_ease_in_out_cubic():
    """Test cubic ease-in-out function"""
    from interpolator import ease_in_out_cubic

    # At t=0 and t=1, should return exact values
    assert ease_in_out_cubic(0.0) == 0.0
    assert ease_in_out_cubic(1.0) == 1.0

    # At t=0.5, should be 0.5 (symmetric)
    assert abs(ease_in_out_cubic(0.5) - 0.5) < 0.001

    # Should be smooth and monotonic
    assert 0 < ease_in_out_cubic(0.25) < 0.5
    assert 0.5 < ease_in_out_cubic(0.75) < 1.0


def test_ease_in_quadratic():
    """Test quadratic ease-in function"""
    from interpolator import ease_in_quadratic

    assert ease_in_quadratic(0.0) == 0.0
    assert ease_in_quadratic(1.0) == 1.0
    assert ease_in_quadratic(0.5) == 0.25  # 0.5^2


def test_ease_out_quadratic():
    """Test quadratic ease-out function"""
    from interpolator import ease_out_quadratic

    assert ease_out_quadratic(0.0) == 0.0
    assert ease_out_quadratic(1.0) == 1.0
    # At t=0.5: 1 - (1-0.5)^2 = 1 - 0.25 = 0.75
    assert ease_out_quadratic(0.5) == 0.75


# Interpolation tests
def test_interpolate_integer_teeth():
    """Test interpolation between integer teeth counts"""
    from interpolator import interpolate_value

    # Linear interpolation between 50 and 100
    assert interpolate_value(50, 100, 0.0, 'linear') == 50
    assert interpolate_value(50, 100, 1.0, 'linear') == 100
    assert interpolate_value(50, 100, 0.5, 'linear') == 75


def test_interpolate_non_integer_teeth():
    """Test that interpolation produces non-integer intermediate values"""
    from interpolator import interpolate_configs

    config_a = {
        "name": "Config A",
        "wheels": [
            {"type": "fixed", "teeth": 100},
            {"type": "moving", "teeth": 50, "pen_offset": 0.5}
        ]
    }

    config_b = {
        "name": "Config B",
        "wheels": [
            {"type": "fixed", "teeth": 84},
            {"type": "moving", "teeth": 21, "pen_offset": 0.7}
        ]
    }

    # Generate 3 intermediate steps
    configs = interpolate_configs(config_a, config_b, steps=5, easing='linear')

    # Should have start, 3 intermediates, and end = 5 configs
    assert len(configs) == 5

    # Middle config should have non-integer teeth
    middle = configs[2]
    moving_wheel = [w for w in middle["wheels"] if w["type"] == "moving"][0]

    # Should be between 21 and 50
    assert 21 < moving_wheel["teeth"] < 50


def test_interpolate_colors():
    """Test RGB color interpolation"""
    from interpolator import interpolate_color

    # Interpolate from red to blue
    red = "#FF0000"
    blue = "#0000FF"

    # At t=0, should be red
    assert interpolate_color(red, blue, 0.0) == "#FF0000"

    # At t=1, should be blue
    assert interpolate_color(red, blue, 1.0) == "#0000FF"

    # At t=0.5, should be purple-ish (middle)
    middle = interpolate_color(red, blue, 0.5)
    assert middle == "#7F007F"  # Half red, half blue


def test_interpolate_radii():
    """Test wheel radii interpolation"""
    from interpolator import interpolate_configs

    config_a = {
        "wheels": [
            {"type": "fixed", "teeth": 100, "radius": 1.0},
            {"type": "moving", "teeth": 50, "radius": 0.5, "pen_offset": 0.5}
        ]
    }

    config_b = {
        "wheels": [
            {"type": "fixed", "teeth": 100, "radius": 1.0},
            {"type": "moving", "teeth": 50, "radius": 0.8, "pen_offset": 0.5}
        ]
    }

    configs = interpolate_configs(config_a, config_b, steps=3, easing='linear')

    # Middle config should have interpolated radius
    middle = configs[1]
    moving_wheel = [w for w in middle["wheels"] if w["type"] == "moving"][0]

    # Should be between 0.5 and 0.8
    assert 0.5 < moving_wheel["radius"] < 0.8


def test_edge_cases_same_config():
    """Test interpolation between identical configurations"""
    from interpolator import interpolate_configs

    config = {
        "wheels": [
            {"type": "fixed", "teeth": 100},
            {"type": "moving", "teeth": 50, "pen_offset": 0.5}
        ]
    }

    configs = interpolate_configs(config, config, steps=3, easing='linear')

    # All configs should be identical
    assert len(configs) == 3
    for c in configs:
        moving_wheel = [w for w in c["wheels"] if w["type"] == "moving"][0]
        assert moving_wheel["teeth"] == 50


def test_rotation_count_interpolation():
    """Test handling of rotation count during interpolation"""
    from interpolator import interpolate_configs

    config_a = {
        "wheels": [
            {"type": "fixed", "teeth": 100},
            {"type": "moving", "teeth": 50, "pen_offset": 0.5}
        ],
        "rotation_count": 1
    }

    config_b = {
        "wheels": [
            {"type": "fixed", "teeth": 84},
            {"type": "moving", "teeth": 21, "pen_offset": 0.7}
        ],
        "rotation_count": 1
    }

    configs = interpolate_configs(config_a, config_b, steps=3, easing='linear')

    # All configs should have rotation_count set
    for c in configs:
        assert "rotation_count" in c
        assert isinstance(c["rotation_count"], int)


def test_interpolation_bounds():
    """Test that t=0 gives config_a and t=1 gives config_b"""
    from interpolator import interpolate_configs

    config_a = {
        "wheels": [
            {"type": "fixed", "teeth": 100},
            {"type": "moving", "teeth": 50, "pen_offset": 0.5}
        ]
    }

    config_b = {
        "wheels": [
            {"type": "fixed", "teeth": 84},
            {"type": "moving", "teeth": 21, "pen_offset": 0.7}
        ]
    }

    configs = interpolate_configs(config_a, config_b, steps=2, easing='linear')

    # First should match config_a
    first_moving = [w for w in configs[0]["wheels"] if w["type"] == "moving"][0]
    assert first_moving["teeth"] == 50
    assert first_moving["pen_offset"] == 0.5

    # Last should match config_b
    last_moving = [w for w in configs[-1]["wheels"] if w["type"] == "moving"][0]
    assert last_moving["teeth"] == 21
    assert last_moving["pen_offset"] == 0.7
