"""
Spirograph - Core mathematics module

This module provides the mathematical functions for generating spirograph patterns.
It supports both hypocycloids (wheel inside) and epicycloids (wheel outside),
as well as non-integer teeth counts for smooth interpolation.
"""

import math
import numpy as np
from typing import List, Tuple, Dict


def calculate_required_rotations(fixed_teeth: float, moving_teeth: float) -> int:
    """
    Calculate the number of rotations needed for the pattern to complete.

    The pattern completes when the moving wheel's center returns to its starting
    position AND the pen returns to the same position on the moving wheel.
    This occurs after r / GCD(R, r) rotations of the center around the fixed wheel,
    where R is the fixed wheel teeth and r is the moving wheel teeth.

    This is equivalent to LCM(R, r) / R rotations.

    Args:
        fixed_teeth: Number of teeth on the fixed (outer) wheel
        moving_teeth: Number of teeth on the moving wheel

    Returns:
        Number of complete rotations (of the center around the fixed wheel)

    Examples:
        >>> calculate_required_rotations(105, 64)
        64
        >>> calculate_required_rotations(96, 36)
        3
        >>> calculate_required_rotations(100, 50)
        1
    """
    # For integer teeth, use GCD
    # For non-integer, round to integers for GCD calculation
    R = int(round(fixed_teeth))
    r = int(round(moving_teeth))

    # Pattern closes after r / GCD(R, r) rotations
    return r // math.gcd(R, r)


def generate_spirograph_simple(
    fixed_teeth: float,
    moving_teeth: float,
    pen_offset: float,
    num_rotations: int,
    points_per_rotation: int = 360
) -> List[Tuple[float, float]]:
    """
    Generate simple 2-wheel spirograph pattern (backward compatibility).

    Args:
        fixed_teeth: Number of teeth on fixed wheel
        moving_teeth: Number of teeth on moving wheel
        pen_offset: Pen offset as fraction of radius
        num_rotations: Number of rotations to draw
        points_per_rotation: Points per rotation

    Returns:
        List of (x, y) coordinate tuples
    """
    R = 1.0
    r = moving_teeth / fixed_teeth
    d = pen_offset * r

    points = []
    total_angle = 2 * math.pi * num_rotations
    num_points = points_per_rotation * num_rotations

    for i in range(num_points + 1):
        t = (i / num_points) * total_angle
        x = (R - r) * math.cos(t) + d * math.cos((R - r) * t / r)
        y = (R - r) * math.sin(t) - d * math.sin((R - r) * t / r)
        points.append((x, y))

    return points


def generate_spirograph_multi(
    wheels: List[Dict],
    num_rotations: int,
    points_per_rotation: int = 360
) -> List[Tuple[float, float]]:
    """
    Generate multi-wheel epicyclic gear train spirograph pattern.

    Supports arbitrary number of wheels in a chain, where each wheel
    (except the fixed one) rolls on a parent wheel.

    Args:
        wheels: List of wheel dictionaries with:
            - type: "fixed" or "moving"
            - teeth: Number of teeth (can be non-integer)
            - radius: Wheel radius (optional, derived from teeth if not provided)
            - parent_index: Index of parent wheel (for moving wheels)
            - pen_offset: Pen offset (only for last wheel with pen)
        num_rotations: Number of rotations to draw
        points_per_rotation: Points per rotation

    Returns:
        List of (x, y) coordinate tuples

    Mathematical approach:
    For each moving wheel in the chain, calculate its position relative to
    its parent using epicyclic motion. The final pen position is the sum
    of all transformations in the chain.
    """
    # Normalize radii relative to first (fixed) wheel
    base_teeth = wheels[0]['teeth']

    # Build wheel data with normalized radii
    wheel_data = []
    for i, wheel in enumerate(wheels):
        radius = wheel.get('radius', wheel['teeth'] / base_teeth)
        if i == 0:
            radius = 1.0  # Normalize fixed wheel to radius 1.0

        wheel_data.append({
            'index': i,
            'type': wheel['type'],
            'teeth': wheel['teeth'],
            'radius': radius,
            'parent_index': wheel.get('parent_index', i - 1 if i > 0 else None),
            'pen_offset': wheel.get('pen_offset', 0.0)
        })

    # Find the wheel with the pen (last moving wheel)
    pen_wheel_index = len(wheel_data) - 1
    pen_offset = wheel_data[pen_wheel_index].get('pen_offset', 0.0)

    points = []
    total_angle = 2 * math.pi * num_rotations
    num_points = points_per_rotation * num_rotations

    for i in range(num_points + 1):
        t = (i / num_points) * total_angle

        # Calculate position by traversing the chain
        x, y = calculate_chain_position(wheel_data, pen_wheel_index, pen_offset, t)
        points.append((x, y))

    return points


def calculate_chain_position(
    wheels: List[Dict],
    target_index: int,
    pen_offset: float,
    t: float
) -> Tuple[float, float]:
    """
    Calculate position of a point on a wheel in an epicyclic chain.

    Args:
        wheels: List of wheel data dictionaries
        target_index: Index of the wheel carrying the pen
        pen_offset: Distance of pen from wheel center
        t: Time parameter (angle in radians)

    Returns:
        (x, y) position tuple
    """
    # Start at origin (fixed wheel center)
    x, y = 0.0, 0.0
    cumulative_angle = 0.0

    # Traverse the chain from fixed wheel to target wheel
    for i in range(1, target_index + 1):
        wheel = wheels[i]
        parent = wheels[wheel['parent_index']]

        R = parent['radius']  # Parent radius
        r = wheel['radius']   # Current wheel radius

        # Center of current wheel relative to parent center
        # The center traces a circle of radius (R - r)
        center_radius = R - r

        # Angular velocity ratio
        # As the wheel rolls, it rotates at rate (R - r) / r relative to parent
        angle = t + cumulative_angle

        # Position of wheel center relative to parent center
        x += center_radius * math.cos(angle)
        y += center_radius * math.sin(angle)

        # Update cumulative angle for next wheel in chain
        # The wheel itself rotates as it rolls
        cumulative_angle += (R - r) / r * t

    # Add pen offset on the final wheel
    if pen_offset > 0:
        pen_radius = pen_offset * wheels[target_index]['radius']
        pen_angle = t + cumulative_angle
        x += pen_radius * math.cos(pen_angle)
        y += pen_radius * math.sin(pen_angle)

    return (x, y)


def generate_spirograph(
    fixed_teeth: float = None,
    moving_teeth: float = None,
    pen_offset: float = None,
    num_rotations: int = None,
    points_per_rotation: int = 360,
    wheels: List[Dict] = None
) -> List[Tuple[float, float]]:
    """
    Generate spirograph pattern coordinates.

    Supports both simple 2-wheel and multi-wheel configurations.

    SIMPLE MODE (2 wheels - backward compatible):
        fixed_teeth: Number of teeth on fixed wheel
        moving_teeth: Number of teeth on moving wheel
        pen_offset: Pen offset as fraction of radius
        num_rotations: Number of rotations
        points_per_rotation: Points per rotation

    MULTI-WHEEL MODE (3+ wheels):
        wheels: List of wheel dictionaries
        num_rotations: Number of rotations
        points_per_rotation: Points per rotation

    Returns:
        List of (x, y) coordinate tuples
    """
    if wheels is not None and len(wheels) > 2:
        # Multi-wheel mode
        return generate_spirograph_multi(wheels, num_rotations, points_per_rotation)
    elif fixed_teeth is not None and moving_teeth is not None:
        # Simple 2-wheel mode (backward compatibility)
        return generate_spirograph_simple(
            fixed_teeth, moving_teeth, pen_offset,
            num_rotations, points_per_rotation
        )
    elif wheels is not None and len(wheels) == 2:
        # 2-wheel via wheels parameter
        return generate_spirograph_simple(
            wheels[0]['teeth'],
            wheels[1]['teeth'],
            wheels[1].get('pen_offset', 0.0),
            num_rotations,
            points_per_rotation
        )
    else:
        raise ValueError("Must provide either (fixed_teeth, moving_teeth, pen_offset) or wheels list")


def get_pattern_info(fixed_teeth: float, moving_teeth: float) -> dict:
    """
    Get information about a spirograph pattern.

    Args:
        fixed_teeth: Number of teeth on fixed wheel
        moving_teeth: Number of teeth on moving wheel

    Returns:
        Dictionary with pattern information including required rotations,
        whether teeth are integers, and GCD if applicable
    """
    R = int(round(fixed_teeth))
    r = int(round(moving_teeth))

    are_integers = (fixed_teeth == R) and (moving_teeth == r)

    info = {
        'fixed_teeth': fixed_teeth,
        'moving_teeth': moving_teeth,
        'are_integers': are_integers,
        'required_rotations': calculate_required_rotations(fixed_teeth, moving_teeth)
    }

    if are_integers:
        info['gcd'] = math.gcd(R, r)

    return info
