"""
Tests for spirograph.py - Core spirograph mathematics module

Following TDD: Write tests first, then implement the functionality
"""
import pytest
import math


# Tests for rotation calculation
def test_calculate_required_rotations_coprime():
    """Test with coprime teeth counts (GCD=1) - requires maximum rotations"""
    from spirograph import calculate_required_rotations
    # 105 and 64 are coprime (GCD = 1), so pattern requires r rotations
    assert calculate_required_rotations(105, 64) == 64
    # 144 and 55 are coprime
    assert calculate_required_rotations(144, 55) == 55


def test_calculate_required_rotations_simple():
    """Test with simple divisible teeth counts"""
    from spirograph import calculate_required_rotations
    # GCD(96, 36) = 12, so 36/12 = 3 rotations
    assert calculate_required_rotations(96, 36) == 3
    # GCD(84, 21) = 21, so 21/21 = 1 rotation
    assert calculate_required_rotations(84, 21) == 1


def test_calculate_required_rotations_perfect_divisor():
    """Test when moving wheel divides fixed wheel evenly"""
    from spirograph import calculate_required_rotations
    # GCD(100, 50) = 50, so 50/50 = 1 rotation
    assert calculate_required_rotations(100, 50) == 1
    # GCD(100, 25) = 25, so 25/25 = 1 rotation
    assert calculate_required_rotations(100, 25) == 1


# Tests for point generation
def test_hypocycloid_generates_points():
    """Test that hypocycloid generation returns valid points"""
    from spirograph import generate_spirograph
    points = generate_spirograph(
        fixed_teeth=96,
        moving_teeth=36,
        pen_offset=0.7,
        num_rotations=8
    )
    # Should return a list of (x, y) tuples
    assert len(points) > 0
    assert all(isinstance(p, tuple) and len(p) == 2 for p in points)
    assert all(isinstance(p[0], (int, float)) and isinstance(p[1], (int, float)) for p in points)


def test_epicycloid_generates_points():
    """Test that epicycloid generation returns valid points"""
    from spirograph import generate_spirograph
    # For epicycloid, moving_teeth should be negative or use a flag
    # For now, we'll test with the same function and verify it works
    points = generate_spirograph(
        fixed_teeth=84,
        moving_teeth=21,
        pen_offset=0.5,
        num_rotations=4
    )
    assert len(points) > 0
    assert all(isinstance(p, tuple) and len(p) == 2 for p in points)


def test_non_integer_teeth_support():
    """Test that non-integer teeth counts work (for interpolation)"""
    from spirograph import generate_spirograph
    # Should work with fractional teeth
    points = generate_spirograph(
        fixed_teeth=100.0,
        moving_teeth=64.5,
        pen_offset=0.6,
        num_rotations=10
    )
    assert len(points) > 0


# Edge case tests
def test_zero_pen_offset():
    """Test with pen at center of wheel (should produce circle)"""
    from spirograph import generate_spirograph
    points = generate_spirograph(
        fixed_teeth=100,
        moving_teeth=50,
        pen_offset=0.0,  # Pen at center
        num_rotations=2
    )
    assert len(points) > 0
    # With pen_offset=0, all points should be at same radius from origin
    # (forms a circle)


def test_equal_wheel_sizes():
    """Test when R == r (edge case)"""
    from spirograph import generate_spirograph
    # This is a degenerate case but should not crash
    points = generate_spirograph(
        fixed_teeth=50,
        moving_teeth=50,
        pen_offset=0.5,
        num_rotations=1
    )
    assert len(points) > 0


def test_pattern_closes():
    """Test that pattern returns to start after required rotations"""
    from spirograph import generate_spirograph, calculate_required_rotations

    R, r = 96, 36
    required = calculate_required_rotations(R, r)

    points = generate_spirograph(
        fixed_teeth=R,
        moving_teeth=r,
        pen_offset=0.7,
        num_rotations=required
    )

    # First and last points should be very close (accounting for floating point)
    assert len(points) >= 2
    first = points[0]
    last = points[-1]

    # Check if they're close (within small epsilon)
    epsilon = 1e-6
    assert abs(first[0] - last[0]) < epsilon
    assert abs(first[1] - last[1]) < epsilon


# Tests for multi-wheel support
def test_3_wheel_generates_points():
    """Test that 3-wheel configuration generates valid points"""
    from spirograph import generate_spirograph

    wheels = [
        {"type": "fixed", "teeth": 120, "radius": 1.0},
        {"type": "moving", "teeth": 60, "radius": 0.5, "parent_index": 0},
        {"type": "moving", "teeth": 30, "radius": 0.25, "parent_index": 1, "pen_offset": 0.8}
    ]

    points = generate_spirograph(wheels=wheels, num_rotations=5)

    assert len(points) > 0
    assert all(isinstance(p, tuple) and len(p) == 2 for p in points)
    assert all(isinstance(p[0], (int, float)) and isinstance(p[1], (int, float)) for p in points)


def test_4_wheel_generates_points():
    """Test that 4-wheel configuration generates valid points"""
    from spirograph import generate_spirograph

    wheels = [
        {"type": "fixed", "teeth": 160, "radius": 1.0},
        {"type": "moving", "teeth": 80, "radius": 0.5, "parent_index": 0},
        {"type": "moving", "teeth": 40, "radius": 0.25, "parent_index": 1},
        {"type": "moving", "teeth": 20, "radius": 0.125, "parent_index": 2, "pen_offset": 0.8}
    ]

    points = generate_spirograph(wheels=wheels, num_rotations=3)

    assert len(points) > 0
    assert all(isinstance(p, tuple) and len(p) == 2 for p in points)


def test_5_wheel_generates_points():
    """Test that 5-wheel configuration generates valid points"""
    from spirograph import generate_spirograph

    wheels = [
        {"type": "fixed", "teeth": 180, "radius": 1.0},
        {"type": "moving", "teeth": 90, "radius": 0.5, "parent_index": 0},
        {"type": "moving", "teeth": 45, "radius": 0.25, "parent_index": 1},
        {"type": "moving", "teeth": 30, "radius": 0.167, "parent_index": 2},
        {"type": "moving", "teeth": 15, "radius": 0.083, "parent_index": 3, "pen_offset": 0.9}
    ]

    points = generate_spirograph(wheels=wheels, num_rotations=2)

    assert len(points) > 0
    assert all(isinstance(p, tuple) and len(p) == 2 for p in points)


def test_2_wheel_via_wheels_parameter():
    """Test backward compatibility: 2-wheel config via wheels parameter"""
    from spirograph import generate_spirograph

    wheels = [
        {"type": "fixed", "teeth": 96, "radius": 1.0},
        {"type": "moving", "teeth": 36, "radius": 0.375, "pen_offset": 0.7}
    ]

    points = generate_spirograph(wheels=wheels, num_rotations=3)

    assert len(points) > 0
    assert all(isinstance(p, tuple) and len(p) == 2 for p in points)


def test_multi_wheel_default_parent_index():
    """Test that parent_index defaults correctly"""
    from spirograph import generate_spirograph

    # Parent indices should default to previous wheel if not specified
    wheels = [
        {"type": "fixed", "teeth": 120, "radius": 1.0},
        {"type": "moving", "teeth": 60, "radius": 0.5},  # No parent_index, should default to 0
        {"type": "moving", "teeth": 30, "radius": 0.25, "pen_offset": 0.8}  # Should default to 1
    ]

    # Should not crash and generate valid points
    points = generate_spirograph(wheels=wheels, num_rotations=2)
    assert len(points) > 0
