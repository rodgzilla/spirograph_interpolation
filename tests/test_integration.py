"""
Integration tests - End-to-end workflow testing

These tests verify that all components work together correctly
"""
import pytest
from config import load_config
from spirograph import generate_spirograph, calculate_required_rotations
from interpolator import interpolate_configs


def test_load_config_and_generate_pattern():
    """
    Integration test: Load config → Generate points → Verify pattern
    """
    # Load configuration
    config = load_config('configs/example_flower.json')

    # Verify config is valid
    assert config['name'] == 'Simple Flower'
    assert config['rotation_count'] == 1  # Auto-calculated

    # Get wheel parameters
    fixed_wheel = next(w for w in config['wheels'] if w['type'] == 'fixed')
    moving_wheel = next(w for w in config['wheels'] if w['type'] == 'moving')

    # Generate pattern
    points = generate_spirograph(
        fixed_teeth=fixed_wheel['teeth'],
        moving_teeth=moving_wheel['teeth'],
        pen_offset=moving_wheel['pen_offset'],
        num_rotations=config['rotation_count']
    )

    # Verify pattern
    assert len(points) > 0
    assert all(len(p) == 2 for p in points)

    # First and last points should be close (pattern closes)
    epsilon = 1e-5
    assert abs(points[0][0] - points[-1][0]) < epsilon
    assert abs(points[0][1] - points[-1][1]) < epsilon


def test_interpolate_and_generate_sequence():
    """
    Integration test: Interpolate configs → Generate intermediates → Verify smoothness
    """
    # Load two configurations
    config_a = load_config('configs/example_flower.json')
    config_b = load_config('configs/example_star.json')

    # Generate interpolated sequence
    configs = interpolate_configs(config_a, config_b, steps=5, easing='ease-in-out')

    # Verify interpolation
    assert len(configs) == 5

    # Verify endpoints match originals
    assert configs[0]['wheels'][1]['teeth'] == config_a['wheels'][1]['teeth']
    assert configs[-1]['wheels'][1]['teeth'] == config_b['wheels'][1]['teeth']

    # Verify smooth progression
    teeth_values = [c['wheels'][1]['teeth'] for c in configs]
    for i in range(len(teeth_values) - 1):
        # Values should be monotonic (increasing or decreasing)
        if teeth_values[0] < teeth_values[-1]:
            assert teeth_values[i] <= teeth_values[i + 1]
        else:
            assert teeth_values[i] >= teeth_values[i + 1]

    # Generate patterns for each config
    for i, config in enumerate(configs):
        fixed_wheel = next(w for w in config['wheels'] if w['type'] == 'fixed')
        moving_wheel = next(w for w in config['wheels'] if w['type'] == 'moving')

        points = generate_spirograph(
            fixed_teeth=fixed_wheel['teeth'],
            moving_teeth=moving_wheel['teeth'],
            pen_offset=moving_wheel['pen_offset'],
            num_rotations=min(config['rotation_count'], 10)  # Limit for performance
        )

        assert len(points) > 0, f"Config {i} produced no points"


def test_full_api_workflow():
    """
    Integration test: API request → Response → Verify output
    """
    from app import app

    app.config['TESTING'] = True
    client = app.test_client()

    # 1. List available configurations
    response = client.get('/api/configs')
    assert response.status_code == 200
    configs = response.get_json()
    assert len(configs) >= 3

    # 2. Load a specific configuration
    config_filename = configs[0]['filename']
    response = client.get(f'/api/config/{config_filename}')
    assert response.status_code == 200
    config = response.get_json()
    assert 'wheels' in config

    # 3. Generate pattern from configuration
    import json
    response = client.post(
        '/api/draw',
        data=json.dumps(config),
        content_type='application/json'
    )
    assert response.status_code == 200
    data = response.get_json()
    assert 'points' in data
    assert len(data['points']) > 0

    # 4. Test interpolation
    config_a = load_config('configs/example_flower.json')
    config_b = load_config('configs/example_star.json')

    response = client.post(
        '/api/interpolate',
        data=json.dumps({
            'config_a': config_a,
            'config_b': config_b,
            'steps': 3,
            'easing': 'linear'
        }),
        content_type='application/json'
    )
    assert response.status_code == 200
    data = response.get_json()
    assert 'configs' in data
    assert len(data['configs']) == 3
