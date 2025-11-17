"""
Flask API for Spirograph Visualization

This module provides a web API for generating spirograph patterns
and serving the interactive visualization interface.
"""

from flask import Flask, render_template, jsonify, request
import os
import json
from typing import Dict, Any, List

from spirograph import generate_spirograph, calculate_required_rotations
from config import load_config, ConfigValidationError, get_wheel_by_type
from interpolator import interpolate_configs

app = Flask(__name__)


@app.route('/')
def index():
    """Serve the main visualization interface"""
    return render_template('index.html')


@app.route('/api/configs', methods=['GET'])
def list_configs():
    """
    List available configuration files.

    Returns:
        JSON array of configuration metadata
    """
    configs_dir = 'configs'
    configs = []

    if os.path.exists(configs_dir):
        for filename in os.listdir(configs_dir):
            if filename.endswith('.json'):
                filepath = os.path.join(configs_dir, filename)
                try:
                    config = load_config(filepath)
                    configs.append({
                        'filename': filename,
                        'name': config.get('name', filename),
                        'path': filepath
                    })
                except Exception as e:
                    # Skip invalid configs
                    continue

    return jsonify(configs)


@app.route('/api/draw', methods=['POST'])
def draw_spirograph():
    """
    Generate spirograph points from a configuration.

    Supports both 2-wheel (backward compatible) and multi-wheel (3+) configurations.

    Request body:
        JSON configuration object

    Returns:
        JSON object with points array and metadata
    """
    try:
        # Get configuration from request
        try:
            config = request.get_json(force=True)
        except Exception:
            return jsonify({'error': 'Invalid JSON'}), 400

        if not config:
            return jsonify({'error': 'No configuration provided'}), 400

        # Validate wheels
        if 'wheels' not in config:
            return jsonify({'error': 'Configuration must have wheels'}), 400

        wheels = config['wheels']
        if len(wheels) < 2:
            return jsonify({'error': 'Configuration must have at least 2 wheels'}), 400

        # Validate wheel types and get first fixed and moving wheels for rotation calculation
        fixed_wheel = None
        moving_wheel = None
        fixed_count = 0
        moving_count = 0

        for wheel in wheels:
            if wheel.get('type') == 'fixed':
                if fixed_wheel is None:
                    fixed_wheel = wheel
                fixed_count += 1
            elif wheel.get('type') == 'moving':
                if moving_wheel is None:
                    moving_wheel = wheel
                moving_count += 1

        if fixed_count == 0:
            return jsonify({'error': 'Configuration must have at least one fixed wheel'}), 400
        if moving_count == 0:
            return jsonify({'error': 'Configuration must have at least one moving wheel'}), 400

        # Validate required fields for rotation calculation
        if 'teeth' not in fixed_wheel:
            return jsonify({'error': 'Fixed wheel missing teeth'}), 400
        if 'teeth' not in moving_wheel:
            return jsonify({'error': 'Moving wheel missing teeth'}), 400

        # Handle rotation count
        rotation_count = config.get('rotation_count', 'auto')
        if rotation_count == 'auto':
            rotation_count = calculate_required_rotations(
                fixed_wheel['teeth'],
                moving_wheel['teeth']
            )

        # Generate points using multi-wheel or simple mode
        points = generate_spirograph(
            wheels=wheels,
            num_rotations=rotation_count
        )

        # Convert to JSON-serializable format
        points_list = [[float(x), float(y)] for x, y in points]

        # Build metadata response
        response = {
            'points': points_list,
            'rotation_count': rotation_count,
            'num_wheels': len(wheels),
            'fixed_teeth': fixed_wheel['teeth'],
            'moving_teeth': moving_wheel['teeth']
        }

        # Add pen_offset if it's a 2-wheel config (backward compatibility)
        if len(wheels) == 2 and 'pen_offset' in moving_wheel:
            response['pen_offset'] = moving_wheel['pen_offset']

        return jsonify(response)

    except ConfigValidationError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f'Internal error: {str(e)}'}), 500


@app.route('/api/interpolate', methods=['POST'])
def interpolate():
    """
    Generate interpolated configurations between two configs.

    Request body:
        {
            "config_a": {...},
            "config_b": {...},
            "steps": 10,
            "easing": "linear"
        }

    Returns:
        JSON object with array of interpolated configurations
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({'error': 'No data provided'}), 400

        config_a = data.get('config_a')
        config_b = data.get('config_b')
        steps = data.get('steps', 10)
        easing = data.get('easing', 'linear')

        if not config_a or not config_b:
            return jsonify({'error': 'Both config_a and config_b are required'}), 400

        # Generate interpolated configs
        configs = interpolate_configs(
            config_a,
            config_b,
            steps=steps,
            easing=easing
        )

        return jsonify({'configs': configs})

    except json.JSONDecodeError:
        return jsonify({'error': 'Invalid JSON'}), 400
    except Exception as e:
        return jsonify({'error': f'Internal error: {str(e)}'}), 500


@app.route('/api/config/<filename>', methods=['GET'])
def get_config(filename):
    """
    Load a specific configuration file.

    Args:
        filename: Name of the configuration file

    Returns:
        JSON configuration object
    """
    try:
        filepath = os.path.join('configs', filename)

        if not os.path.exists(filepath):
            return jsonify({'error': 'Configuration not found'}), 404

        config = load_config(filepath)
        return jsonify(config)

    except ConfigValidationError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f'Internal error: {str(e)}'}), 500


if __name__ == '__main__':
    app.run(debug=True, port=5000)
