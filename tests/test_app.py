"""
Tests for app.py - Flask API endpoints

Following TDD: Write tests first, then implement the functionality
"""
import pytest
import json
import os


@pytest.fixture
def client():
    """Create a test client for the Flask app"""
    from app import app
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def test_index_route_returns_200(client):
    """Test that main page loads successfully"""
    response = client.get('/')
    assert response.status_code == 200
    assert b'html' in response.data.lower()


def test_api_configs_lists_available(client):
    """Test that /api/configs returns list of configurations"""
    response = client.get('/api/configs')
    assert response.status_code == 200

    data = json.loads(response.data)
    assert isinstance(data, list)
    assert len(data) >= 3  # We have 3 example configs

    # Check structure
    for config in data:
        assert 'filename' in config
        assert 'name' in config


def test_api_draw_generates_points(client):
    """Test that /api/draw generates spirograph points"""
    config = {
        "wheels": [
            {"type": "fixed", "teeth": 96, "radius": 1.0},
            {"type": "moving", "teeth": 36, "radius": 0.375, "pen_offset": 0.7}
        ],
        "rotation_count": 3
    }

    response = client.post('/api/draw',
                          data=json.dumps(config),
                          content_type='application/json')

    assert response.status_code == 200
    data = json.loads(response.data)

    assert 'points' in data
    assert isinstance(data['points'], list)
    assert len(data['points']) > 0

    # Each point should be [x, y]
    assert all(len(p) == 2 for p in data['points'])


def test_api_draw_with_invalid_config(client):
    """Test error handling with invalid configuration"""
    # Missing required field
    invalid_config = {
        "wheels": [
            {"type": "fixed", "teeth": 100}
            # Missing moving wheel
        ]
    }

    response = client.post('/api/draw',
                          data=json.dumps(invalid_config),
                          content_type='application/json')

    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data


def test_rotation_count_auto_calculation(client):
    """Test that API auto-calculates rotation count"""
    config = {
        "wheels": [
            {"type": "fixed", "teeth": 96},
            {"type": "moving", "teeth": 36, "pen_offset": 0.7}
        ],
        "rotation_count": "auto"
    }

    response = client.post('/api/draw',
                          data=json.dumps(config),
                          content_type='application/json')

    assert response.status_code == 200
    data = json.loads(response.data)

    # Should have auto-calculated to 3 rotations
    assert 'rotation_count' in data
    assert data['rotation_count'] == 3


def test_api_error_handling(client):
    """Test API error responses"""
    # Send invalid JSON
    response = client.post('/api/draw',
                          data='not valid json',
                          content_type='application/json')

    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data


def test_api_interpolate(client):
    """Test interpolation endpoint"""
    request_data = {
        "config_a": {
            "wheels": [
                {"type": "fixed", "teeth": 100},
                {"type": "moving", "teeth": 50, "pen_offset": 0.5}
            ]
        },
        "config_b": {
            "wheels": [
                {"type": "fixed", "teeth": 84},
                {"type": "moving", "teeth": 21, "pen_offset": 0.7}
            ]
        },
        "steps": 5,
        "easing": "linear"
    }

    response = client.post('/api/interpolate',
                          data=json.dumps(request_data),
                          content_type='application/json')

    assert response.status_code == 200
    data = json.loads(response.data)

    assert 'configs' in data
    assert len(data['configs']) == 5


# Tests for multi-wheel API support
def test_api_draw_3_wheel_config(client):
    """Test API with 3-wheel configuration"""
    config = {
        "wheels": [
            {"type": "fixed", "teeth": 120, "radius": 1.0},
            {"type": "moving", "teeth": 60, "radius": 0.5, "parent_index": 0},
            {"type": "moving", "teeth": 30, "radius": 0.25, "parent_index": 1, "pen_offset": 0.8}
        ],
        "rotation_count": 5
    }

    response = client.post('/api/draw',
                          data=json.dumps(config),
                          content_type='application/json')

    assert response.status_code == 200
    data = json.loads(response.data)

    assert 'points' in data
    assert isinstance(data['points'], list)
    assert len(data['points']) > 0
    assert data['num_wheels'] == 3


def test_api_draw_4_wheel_config(client):
    """Test API with 4-wheel configuration"""
    config = {
        "wheels": [
            {"type": "fixed", "teeth": 160, "radius": 1.0},
            {"type": "moving", "teeth": 80, "radius": 0.5, "parent_index": 0},
            {"type": "moving", "teeth": 40, "radius": 0.25, "parent_index": 1},
            {"type": "moving", "teeth": 20, "radius": 0.125, "parent_index": 2, "pen_offset": 0.8}
        ],
        "rotation_count": 3
    }

    response = client.post('/api/draw',
                          data=json.dumps(config),
                          content_type='application/json')

    assert response.status_code == 200
    data = json.loads(response.data)

    assert 'points' in data
    assert data['num_wheels'] == 4


def test_api_draw_5_wheel_config(client):
    """Test API with 5-wheel configuration"""
    config = {
        "wheels": [
            {"type": "fixed", "teeth": 180, "radius": 1.0},
            {"type": "moving", "teeth": 90, "radius": 0.5, "parent_index": 0},
            {"type": "moving", "teeth": 45, "radius": 0.25, "parent_index": 1},
            {"type": "moving", "teeth": 30, "radius": 0.167, "parent_index": 2},
            {"type": "moving", "teeth": 15, "radius": 0.083, "parent_index": 3, "pen_offset": 0.9}
        ],
        "rotation_count": 2
    }

    response = client.post('/api/draw',
                          data=json.dumps(config),
                          content_type='application/json')

    assert response.status_code == 200
    data = json.loads(response.data)

    assert 'points' in data
    assert data['num_wheels'] == 5


def test_api_draw_multi_wheel_auto_rotation(client):
    """Test that API auto-calculates rotation count for multi-wheel"""
    config = {
        "wheels": [
            {"type": "fixed", "teeth": 120, "radius": 1.0},
            {"type": "moving", "teeth": 60, "radius": 0.5, "parent_index": 0},
            {"type": "moving", "teeth": 30, "radius": 0.25, "parent_index": 1, "pen_offset": 0.8}
        ],
        "rotation_count": "auto"
    }

    response = client.post('/api/draw',
                          data=json.dumps(config),
                          content_type='application/json')

    assert response.status_code == 200
    data = json.loads(response.data)

    # Should have auto-calculated rotation count
    assert 'rotation_count' in data
    assert isinstance(data['rotation_count'], int)
    assert data['rotation_count'] > 0


def test_api_draw_reject_less_than_2_wheels(client):
    """Test that API rejects configs with less than 2 wheels"""
    config = {
        "wheels": [
            {"type": "fixed", "teeth": 100}
        ],
        "rotation_count": 5
    }

    response = client.post('/api/draw',
                          data=json.dumps(config),
                          content_type='application/json')

    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data


def test_api_draw_reject_no_fixed_wheel(client):
    """Test that API rejects configs without fixed wheels"""
    config = {
        "wheels": [
            {"type": "moving", "teeth": 100, "parent_index": 0},
            {"type": "moving", "teeth": 50, "parent_index": 0, "pen_offset": 0.5}
        ],
        "rotation_count": 5
    }

    response = client.post('/api/draw',
                          data=json.dumps(config),
                          content_type='application/json')

    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data


def test_api_draw_reject_no_moving_wheel(client):
    """Test that API rejects configs without moving wheels"""
    config = {
        "wheels": [
            {"type": "fixed", "teeth": 100},
            {"type": "fixed", "teeth": 50}
        ],
        "rotation_count": 5
    }

    response = client.post('/api/draw',
                          data=json.dumps(config),
                          content_type='application/json')

    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data


def test_api_draw_2_wheel_backward_compatible(client):
    """Test that 2-wheel configs remain backward compatible"""
    config = {
        "wheels": [
            {"type": "fixed", "teeth": 96, "radius": 1.0},
            {"type": "moving", "teeth": 36, "radius": 0.375, "pen_offset": 0.7}
        ],
        "rotation_count": 3
    }

    response = client.post('/api/draw',
                          data=json.dumps(config),
                          content_type='application/json')

    assert response.status_code == 200
    data = json.loads(response.data)

    assert 'points' in data
    assert data['num_wheels'] == 2
    assert 'pen_offset' in data  # Backward compatibility: pen_offset in response for 2-wheel
    assert data['pen_offset'] == 0.7
