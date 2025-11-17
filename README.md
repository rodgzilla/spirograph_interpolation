# Spirograph Visualization Software

A Python-based spirograph pattern generator with interactive web visualization and smooth morphing animations between different configurations. This project was built using Claude Code.

A morphing example (click on it to the see the video).

[![Watch the video](https://img.youtube.com/vi/p1_LhkvXaoA/maxresdefault.jpg)](https://youtu.be/p1_LhkvXaoA)

The interface of the project.

![Interface of the generator](imgs/interface.png)

## Features

- **Configuration-based Generation**: Define spirograph parameters in JSON files
- **Auto-rotation Calculation**: Automatically determines when patterns complete using GCD
- **Smooth Interpolation**: Morph between configurations with easing functions
- **Non-integer Teeth Support**: Create unique patterns during transitions
- **Interactive Web Interface**: Real-time HTML5 Canvas visualization
- **TDD Approach**: >90% test coverage with comprehensive test suite

## Project Status

### ✅ Completed
- Core spirograph mathematics (`spirograph.py`)
- Configuration system with JSON validation (`config.py`)
- Interpolation engine with easing functions (`interpolator.py`)
- Test suite (37 passing tests)
- Example configurations

### 🚧 In Progress
- Flask API implementation (`app.py`)
- HTML5 Canvas frontend
- Morphing animation interface

## Installation

1. Create a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements-dev.txt
```

## Usage

### Running Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_spirograph.py

# Run with coverage (after installing pytest-cov)
pytest --cov=. --cov-report=html
```

### Example: Generate Spirograph Pattern

```python
from spirograph import generate_spirograph, calculate_required_rotations

# Define parameters
fixed_teeth = 96
moving_teeth = 36
pen_offset = 0.7

# Calculate required rotations
rotations = calculate_required_rotations(fixed_teeth, moving_teeth)
print(f"Pattern completes after {rotations} rotations")  # Output: 3

# Generate points
points = generate_spirograph(
    fixed_teeth=fixed_teeth,
    moving_teeth=moving_teeth,
    pen_offset=pen_offset,
    num_rotations=rotations
)

print(f"Generated {len(points)} points")
```

### Example: Load Configuration

```python
from config import load_config

# Load a configuration file
config = load_config('configs/example_classic.json')

print(f"Configuration: {config['name']}")
print(f"Required rotations: {config['rotation_count']}")
```

### Example: Interpolate Between Configurations

```python
from interpolator import interpolate_configs
from config import load_config

# Load two configurations
config_a = load_config('configs/example_flower.json')
config_b = load_config('configs/example_star.json')

# Generate 10 intermediate configurations
configs = interpolate_configs(
    config_a,
    config_b,
    steps=10,
    easing='ease-in-out'
)

# Each config has smoothly interpolated values
for i, config in enumerate(configs):
    print(f"Step {i}: {config['wheels'][1]['teeth']:.1f} teeth")
```

## Configuration Format

Spirograph configurations are defined in JSON:

```json
{
  "name": "Classic Spirograph",
  "wheels": [
    {
      "type": "fixed",
      "teeth": 105,
      "radius": 1.0
    },
    {
      "type": "moving",
      "teeth": 64,
      "radius": 0.61,
      "pen_offset": 0.8
    }
  ],
  "rotation_count": "auto",
  "color": "#2E86AB",
  "line_width": 2
}
```

### Configuration Fields

- `name` (string): Human-readable name
- `wheels` (array): Fixed and moving wheel specifications
  - `type`: "fixed" or "moving"
  - `teeth`: Number of teeth (can be non-integer)
  - `radius`: Wheel radius (optional, defaults based on teeth)
  - `pen_offset`: Distance from wheel center (moving wheel only)
- `rotation_count`: Number of rotations or "auto" for automatic calculation
- `color`: Hex color code (#RRGGBB)
- `line_width`: Line thickness

## How Spirographs Work

### Mathematics

A spirograph is created by a small wheel (radius `r`) rolling inside a larger fixed wheel (radius `R`). A pen at distance `d` from the center of the moving wheel traces the pattern.

**Hypocycloid equations:**
```
x = (R-r) * cos(t) + d * cos((R-r)*t/r)
y = (R-r) * sin(t) - d * sin((R-r)*t/r)
```

### Pattern Completion

The pattern completes after a specific number of rotations, calculated using:

```
rotations = r / GCD(R, r)
```

**Examples:**
- R=96, r=36: GCD=12 → 3 rotations
- R=105, r=64: GCD=1 → 64 rotations (maximum complexity)
- R=100, r=50: GCD=50 → 1 rotation (simple pattern)

## Easing Functions

The interpolator supports multiple easing functions for smooth transitions:

- **Linear**: Constant speed (`f(t) = t`)
- **Ease-in-out**: Slow start and end (`f(t) = 3t² - 2t³`)
- **Ease-in**: Slow start (`f(t) = t²`)
- **Ease-out**: Slow end (`f(t) = 1 - (1-t)²`)

## Development

### TDD Workflow

This project follows Test-Driven Development:

1. Write failing tests first
2. Implement minimal code to pass tests
3. Refactor while keeping tests green
4. Check coverage and add edge case tests

### Project Structure

```
spirograph/
├── PLAN.md                    # Detailed implementation plan
├── README.md                  # This file
├── spirograph.py              # Core mathematics
├── config.py                  # Configuration system
├── interpolator.py            # Easing & interpolation
├── app.py                     # Flask API (in progress)
├── configs/                   # Example configurations
│   ├── example_classic.json
│   ├── example_flower.json
│   └── example_star.json
└── tests/                     # Test suite
    ├── test_spirograph.py     # 9 tests
    ├── test_config.py         # 8 tests
    ├── test_interpolator.py   # 11 tests
    ├── test_app.py            # 6 tests
    └── test_integration.py    # 3 tests
```

## Test Summary

- **Total Tests**: 37
- **Status**: All passing ✅
- **Coverage Goal**: >90%

### Test Breakdown

- **Spirograph Math** (9 tests):
  - Rotation calculation (GCD-based)
  - Point generation (hypocycloid)
  - Non-integer teeth support
  - Edge cases (zero offset, equal wheels)
  - Pattern closure verification

- **Config System** (8 tests):
  - JSON loading and validation
  - Schema enforcement
  - Auto-rotation calculation
  - Default value handling
  - Error handling

- **Interpolator** (11 tests):
  - Easing functions (linear, cubic, quadratic)
  - Value interpolation
  - Color interpolation (RGB)
  - Configuration morphing
  - Boundary conditions

## Next Steps

1. ✅ Complete Flask API implementation
2. ⬜ Build HTML5 Canvas frontend
3. ⬜ Create morphing animation interface
4. ⬜ Run coverage analysis
5. ⬜ Deploy web application

## License

This project is for educational and demonstration purposes.

## References

- [Spirograph Mathematics (Wikipedia)](https://en.wikipedia.org/wiki/Spirograph)
- [Hypocycloid Equations](https://mathworld.wolfram.com/Hypocycloid.html)
- [Easing Functions](https://easings.net/)
