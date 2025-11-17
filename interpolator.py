"""
Interpolator - Interpolation and easing functions module

This module provides easing functions and configuration interpolation
for smooth morphing between spirograph patterns.
"""

import copy
from typing import Dict, Any, List, Callable
from spirograph import calculate_required_rotations


# Easing Functions
def linear(t: float) -> float:
    """
    Linear easing function: f(t) = t

    Args:
        t: Parameter between 0 and 1

    Returns:
        Eased value between 0 and 1
    """
    return t


def ease_in_out_cubic(t: float) -> float:
    """
    Cubic ease-in-out function: f(t) = 3t² - 2t³

    Starts slow, speeds up in the middle, ends slow.

    Args:
        t: Parameter between 0 and 1

    Returns:
        Eased value between 0 and 1
    """
    return 3 * t * t - 2 * t * t * t


def ease_in_quadratic(t: float) -> float:
    """
    Quadratic ease-in function: f(t) = t²

    Starts slow, accelerates.

    Args:
        t: Parameter between 0 and 1

    Returns:
        Eased value between 0 and 1
    """
    return t * t


def ease_out_quadratic(t: float) -> float:
    """
    Quadratic ease-out function: f(t) = 1 - (1-t)²

    Starts fast, decelerates.

    Args:
        t: Parameter between 0 and 1

    Returns:
        Eased value between 0 and 1
    """
    return 1 - (1 - t) * (1 - t)


# Easing function registry
EASING_FUNCTIONS: Dict[str, Callable[[float], float]] = {
    'linear': linear,
    'ease-in-out': ease_in_out_cubic,
    'ease-in': ease_in_quadratic,
    'ease-out': ease_out_quadratic,
}


def get_easing_function(name: str) -> Callable[[float], float]:
    """
    Get an easing function by name.

    Args:
        name: Name of the easing function

    Returns:
        Easing function

    Raises:
        ValueError: If easing function name is not recognized
    """
    if name not in EASING_FUNCTIONS:
        raise ValueError(
            f"Unknown easing function '{name}'. "
            f"Available: {', '.join(EASING_FUNCTIONS.keys())}"
        )
    return EASING_FUNCTIONS[name]


def interpolate_value(
    a: float,
    b: float,
    t: float,
    easing: str = 'linear'
) -> float:
    """
    Interpolate between two numeric values.

    Args:
        a: Start value
        b: End value
        t: Parameter between 0 and 1
        easing: Name of easing function to use

    Returns:
        Interpolated value
    """
    easing_func = get_easing_function(easing)
    t_eased = easing_func(t)
    return a + (b - a) * t_eased


def interpolate_color(
    color_a: str,
    color_b: str,
    t: float,
    easing: str = 'linear'
) -> str:
    """
    Interpolate between two hex colors.

    Args:
        color_a: Start color in hex format (#RRGGBB)
        color_b: End color in hex format (#RRGGBB)
        t: Parameter between 0 and 1
        easing: Name of easing function to use

    Returns:
        Interpolated color in hex format
    """
    # Convert hex to RGB
    r1 = int(color_a[1:3], 16)
    g1 = int(color_a[3:5], 16)
    b1 = int(color_a[5:7], 16)

    r2 = int(color_b[1:3], 16)
    g2 = int(color_b[3:5], 16)
    b2 = int(color_b[5:7], 16)

    # Interpolate each channel
    r = int(interpolate_value(r1, r2, t, easing))
    g = int(interpolate_value(g1, g2, t, easing))
    b = int(interpolate_value(b1, b2, t, easing))

    # Convert back to hex
    return f"#{r:02X}{g:02X}{b:02X}"


def interpolate_wheel(
    wheel_a: Dict[str, Any],
    wheel_b: Dict[str, Any],
    t: float,
    easing: str = 'linear'
) -> Dict[str, Any]:
    """
    Interpolate between two wheel configurations.

    Args:
        wheel_a: Start wheel configuration
        wheel_b: End wheel configuration
        t: Parameter between 0 and 1
        easing: Name of easing function to use

    Returns:
        Interpolated wheel configuration
    """
    result = {"type": wheel_a["type"]}

    # Interpolate teeth
    result["teeth"] = interpolate_value(
        wheel_a["teeth"],
        wheel_b["teeth"],
        t,
        easing
    )

    # Interpolate radius if present in both
    if "radius" in wheel_a and "radius" in wheel_b:
        result["radius"] = interpolate_value(
            wheel_a["radius"],
            wheel_b["radius"],
            t,
            easing
        )
    elif "radius" in wheel_a:
        result["radius"] = wheel_a["radius"]
    elif "radius" in wheel_b:
        result["radius"] = wheel_b["radius"]

    # Interpolate pen_offset if present (for moving wheels)
    if "pen_offset" in wheel_a and "pen_offset" in wheel_b:
        result["pen_offset"] = interpolate_value(
            wheel_a["pen_offset"],
            wheel_b["pen_offset"],
            t,
            easing
        )
    elif "pen_offset" in wheel_a:
        result["pen_offset"] = wheel_a["pen_offset"]
    elif "pen_offset" in wheel_b:
        result["pen_offset"] = wheel_b["pen_offset"]

    return result


def interpolate_configs(
    config_a: Dict[str, Any],
    config_b: Dict[str, Any],
    steps: int,
    easing: str = 'linear',
    rotation_strategy: str = 'auto'
) -> List[Dict[str, Any]]:
    """
    Interpolate between two spirograph configurations.

    Args:
        config_a: Start configuration
        config_b: End configuration
        steps: Number of configurations to generate (including start and end)
        easing: Name of easing function to use
        rotation_strategy: How to handle rotation_count:
            - 'auto': Recalculate for each intermediate config
            - 'max': Use maximum of start and end
            - 'fixed': Use a fixed number (50)

    Returns:
        List of interpolated configurations
    """
    if steps < 2:
        raise ValueError("steps must be at least 2")

    configs = []

    for i in range(steps):
        # Calculate interpolation parameter
        t = i / (steps - 1) if steps > 1 else 0.0

        # Create interpolated config
        config = {}

        # Interpolate name
        if "name" in config_a or "name" in config_b:
            name_a = config_a.get("name", "")
            name_b = config_b.get("name", "")
            if t == 0:
                config["name"] = name_a
            elif t == 1:
                config["name"] = name_b
            else:
                config["name"] = f"{name_a} → {name_b} ({t:.1%})"

        # Interpolate wheels
        wheels_a = config_a.get("wheels", [])
        wheels_b = config_b.get("wheels", [])

        # Match wheels by type
        fixed_a = next((w for w in wheels_a if w.get("type") == "fixed"), {})
        fixed_b = next((w for w in wheels_b if w.get("type") == "fixed"), {})
        moving_a = next((w for w in wheels_a if w.get("type") == "moving"), {})
        moving_b = next((w for w in wheels_b if w.get("type") == "moving"), {})

        config["wheels"] = [
            interpolate_wheel(fixed_a, fixed_b, t, easing),
            interpolate_wheel(moving_a, moving_b, t, easing)
        ]

        # Handle rotation_count
        if rotation_strategy == 'auto':
            # Recalculate for interpolated teeth
            fixed = config["wheels"][0]
            moving = config["wheels"][1]
            config["rotation_count"] = calculate_required_rotations(
                fixed["teeth"],
                moving["teeth"]
            )
        elif rotation_strategy == 'max':
            rot_a = config_a.get("rotation_count", 1)
            rot_b = config_b.get("rotation_count", 1)
            config["rotation_count"] = max(rot_a, rot_b)
        elif rotation_strategy == 'fixed':
            config["rotation_count"] = 50
        else:
            # Default: use provided or calculate
            if "rotation_count" in config_a:
                config["rotation_count"] = config_a["rotation_count"]
            else:
                fixed = config["wheels"][0]
                moving = config["wheels"][1]
                config["rotation_count"] = calculate_required_rotations(
                    fixed["teeth"],
                    moving["teeth"]
                )

        # Interpolate color if present
        if "color" in config_a and "color" in config_b:
            config["color"] = interpolate_color(
                config_a["color"],
                config_b["color"],
                t,
                easing
            )
        elif "color" in config_a:
            config["color"] = config_a["color"]
        elif "color" in config_b:
            config["color"] = config_b["color"]

        # Interpolate line_width if present
        if "line_width" in config_a and "line_width" in config_b:
            config["line_width"] = interpolate_value(
                config_a["line_width"],
                config_b["line_width"],
                t,
                easing
            )
        elif "line_width" in config_a:
            config["line_width"] = config_a["line_width"]
        elif "line_width" in config_b:
            config["line_width"] = config_b["line_width"]

        configs.append(config)

    return configs
