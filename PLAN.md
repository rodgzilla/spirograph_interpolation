# Spirograph Visualization Software - Implementation Plan (TDD Approach)

## Overview
Build a Python-based spirograph visualization system with two main features:
1. **Configuration-based generation**: Users define spirograph parameters in JSON files
2. **Interpolation & morphing**: Smooth transitions between different configurations

**Development Methodology**: Test-Driven Development (TDD)
- Write tests first, then implement features
- Maintain high test coverage (>90% goal)
- Continuous validation of mathematical correctness

## Technology Stack
- **Language**: Python 3.10+
- **Web Framework**: Flask
- **Mathematics**: NumPy
- **Frontend**: HTML5 Canvas, JavaScript
- **Configuration**: JSON with jsonschema validation
- **Testing**: pytest, pytest-cov (coverage), hypothesis (property-based testing - optional)

---

## Phase 1: Core Spirograph Generation (TDD)

### 1. Project Setup
- Create Python virtual environment
- Install dependencies:
  - `flask` - Web server
  - `numpy` - Mathematical calculations
  - `jsonschema` - Configuration validation
  - `pytest` - Testing framework
  - `pytest-cov` - Code coverage
  - `hypothesis` - Property-based testing (optional)
- Set up project structure with `tests/` directory

### 2. Spirograph Mathematics Module (`spirograph.py`) - TDD

**Tests First** (`tests/test_spirograph.py`):
```python
# Test cases to write BEFORE implementation:
- test_calculate_completion_rotations()  # LCM/GCD calculation
- test_epicycloid_point_generation()     # External wheel
- test_hypocycloid_point_generation()    # Internal wheel
- test_non_integer_teeth_support()       # Fractional teeth
- test_pattern_symmetry()                # Mathematical properties
- test_zero_pen_offset()                 # Edge case
- test_equal_wheel_sizes()               # Edge case
```

**Implementation Features**:
- **Parametric equations** for spirograph curves:
  - Epicycloid (wheel rolling outside):
    - `x = (R+r)*cos(t) - d*cos((R+r)*t/r)`
    - `y = (R+r)*sin(t) - d*sin((R+r)*t/r)`
  - Hypocycloid (wheel rolling inside):
    - `x = (R-r)*cos(t) + d*cos((R-r)*t/r)`
    - `y = (R-r)*sin(t) - d*sin((R-r)*t/r)`

  Where:
  - `R` = radius of fixed wheel
  - `r` = radius of moving wheel
  - `d` = pen offset from center of moving wheel
  - `t` = parameter (angle)

- **Rotation calculation**:
  ```python
  def calculate_required_rotations(fixed_teeth, moving_teeth):
      """
      Calculate number of rotations needed to complete the pattern.
      Uses GCD to determine when the pattern repeats.

      Formula: R / GCD(R, r)

      Examples:
      - R=105, r=64: GCD=1 → 105 rotations
      - R=96, r=36: GCD=12 → 8 rotations
      - R=100, r=50: GCD=50 → 2 rotations
      """
      return fixed_teeth // math.gcd(fixed_teeth, moving_teeth)
  ```

- **Multi-wheel support**: Fixed wheel + moving wheels
- **Key parameters**:
  - Number of teeth per wheel
  - Wheel radii (derived from teeth ratios)
  - Pen position/offset
  - Auto-calculated rotation count
- **Non-integer teeth support** for interpolation

### 3. Configuration System (`config.py`) - TDD

**Tests First** (`tests/test_config.py`):
```python
- test_load_valid_json_config()
- test_reject_invalid_schema()
- test_calculate_auto_rotations()        # Auto-compute from teeth
- test_default_values()
- test_missing_required_fields()
- test_teeth_count_validation()          # Must be positive
- test_invalid_json_syntax()
- test_color_format_validation()
```

**JSON Schema**:
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

**Configuration Fields**:
- `name` (string): Human-readable name for the configuration
- `wheels` (array): List of wheel specifications
  - `type` (string): "fixed" or "moving"
  - `teeth` (number): Number of teeth (can be non-integer for interpolation)
  - `radius` (number): Wheel radius (typically derived from teeth, but can be specified)
  - `pen_offset` (number, moving wheels only): Distance from wheel center to pen (0.0-1.0)
- `rotation_count` (number or "auto"): Number of rotations to draw
  - "auto": Calculate automatically using GCD formula
  - number: Specific rotation count (useful for incomplete patterns or animations)
- `color` (string): Hex color code for the line
- `line_width` (number): Width of the drawn line

**Features**:
- Auto-calculate `rotation_count` using GCD formula when set to "auto"
- Load and validate JSON configurations
- Provide default configurations for testing
- Comprehensive error messages with line numbers
- Schema validation using jsonschema

### 4. Web-Based Interactive Viewer

**Backend Tests** (`tests/test_app.py`):
```python
- test_index_route_returns_200()
- test_api_configs_lists_available()
- test_api_draw_generates_points()
- test_api_draw_with_invalid_config()
- test_rotation_count_auto_calculation()
- test_api_error_handling()
```

**Backend** (`app.py`):
Flask server with routes:
- `GET /` - Main viewer interface (serves HTML)
- `GET /api/configs` - List available configurations from configs/ directory
- `POST /api/draw` - Generate spirograph coordinates
  - Request body: JSON configuration
  - Response: Array of (x, y) coordinates
- `POST /api/interpolate` - Generate interpolated configurations
  - Request body: Two configs + number of steps + easing function
  - Response: Array of intermediate configurations

**Frontend**:
- `templates/index.html` - Main interface
- `static/js/canvas_renderer.js` - Canvas drawing logic
  - Real-time animation as curves are drawn
  - Responsive canvas sizing
  - Animation speed control
  - Display current rotation count vs. required
  - Show when pattern completes
- `static/css/style.css` - Styling

**Interactive Controls**:
- **Configuration Loading**:
  - Dropdown to select from available configs
  - Upload custom JSON file
  - Live JSON editor (optional)
- **Animation Controls**:
  - Play/pause button
  - Speed slider (0.1x to 10x)
  - Reset button
  - Step forward/backward buttons
- **Progress Display**:
  - Current rotation / Total rotations
  - Progress bar
  - Pattern completion indicator
- **Visual Options**:
  - Background color
  - Show/hide wheels (optional)
  - Clear canvas button

---

## Phase 2: Interpolation & Morphing (TDD)

### 5. Interpolation Engine (`interpolator.py`) - TDD

**Tests First** (`tests/test_interpolator.py`):
```python
- test_linear_easing()
- test_ease_in_out_cubic()
- test_ease_in_quadratic()
- test_ease_out_quadratic()
- test_interpolate_integer_teeth()
- test_interpolate_non_integer_teeth()
- test_interpolate_colors()
- test_interpolate_radii()
- test_edge_cases_same_config()
- test_rotation_count_interpolation()
- test_interpolation_bounds()           # t=0 gives config_a, t=1 gives config_b
```

**Easing Functions**:
Mathematical functions that control interpolation speed:

1. **Linear**: `f(t) = t`
   - Constant speed throughout

2. **Ease-in-out (cubic)**: `f(t) = 3t² - 2t³`
   - Slow at start and end, fast in middle

3. **Ease-in (quadratic)**: `f(t) = t²`
   - Slow start, accelerates

4. **Ease-out (quadratic)**: `f(t) = 1 - (1-t)²`
   - Fast start, decelerates

5. **Elastic** (optional): Bouncy effect
   - More complex formula, good for creative transitions

**Interpolation Logic**:
```python
def interpolate_configs(config_a, config_b, steps, easing_func='ease-in-out'):
    """
    Generate N intermediate configurations between A and B.

    Parameters:
    - config_a: Starting configuration (dict)
    - config_b: Ending configuration (dict)
    - steps: Number of intermediate steps (int)
    - easing_func: Name of easing function (str)

    Returns:
    - List of configurations including start and end

    Interpolates:
    - Teeth counts (supports non-integer values like 64.5)
    - Wheel radii
    - Pen offsets
    - Colors (RGB interpolation, not hex)
    - Line widths

    Special handling:
    - Rotation count: Use "auto" for each intermediate config OR
                     use max(start, end) rotation count
    - Non-integer teeth may result in non-repeating patterns
    """
    pass
```

**Color Interpolation**:
- Convert hex colors to RGB
- Interpolate each channel separately
- Convert back to hex for output

**Handling Non-Integer Teeth**:
- During interpolation, teeth can be 64.5, 37.2, etc.
- Mathematical formulas still work
- Pattern may never "complete" (GCD undefined for non-integers)
- Solutions:
  1. Set rotation_count to max of start/end configs
  2. Use a fixed high number (e.g., 100 rotations)
  3. Let user specify in interpolation parameters

### 6. Animation System - TDD

**Tests** (`tests/test_animation.py`):
```python
- test_generate_frame_sequence()
- test_morphing_step_count()
- test_animation_timing()
- test_sequence_consistency()
```

**Morphing Viewer Interface**:
- Load two configurations (start & end)
- Select number of intermediate steps (default: 30)
- Choose easing function from dropdown
- Visualize smooth transition frame by frame
- Option to play as continuous animation
- Display configuration differences

**Animation Features**:
- Smooth transitions between patterns
- Configurable frame rate
- Loop option (A→B→A continuous)
- Pause on intermediate frames
- Display current configuration parameters

---

## Project Structure

```
spirograph/
├── README.md                          # Project documentation
├── PLAN.md                            # This file - implementation plan
├── requirements.txt                   # Python dependencies
├── requirements-dev.txt               # Development dependencies (pytest, etc.)
├── pytest.ini                         # Pytest configuration
├── .gitignore                         # Git ignore file
├── app.py                             # Flask web server
├── spirograph.py                      # Core spirograph mathematics
├── config.py                          # Configuration loading & validation
├── interpolator.py                    # Interpolation & easing functions
├── static/
│   ├── js/
│   │   └── canvas_renderer.js        # Canvas drawing & animation
│   └── css/
│       └── style.css                 # Styles
├── templates/
│   └── index.html                    # Main web interface
├── configs/                           # Example configurations
│   ├── example_classic.json
│   ├── example_flower.json
│   └── example_star.json
└── tests/                             # TDD test suite
    ├── __init__.py
    ├── test_spirograph.py            # Math module tests
    ├── test_config.py                # Config system tests
    ├── test_interpolator.py          # Interpolation tests
    ├── test_app.py                   # Flask API tests
    └── test_integration.py           # End-to-end tests
```

---

## TDD Implementation Workflow

### Red-Green-Refactor Cycle

For each feature, follow this cycle:

1. **🔴 RED**: Write a failing test
   - Think about the API/interface first
   - Write test that uses the feature
   - Run test → it should fail (feature doesn't exist yet)

2. **🟢 GREEN**: Write minimal code to pass
   - Implement just enough to make test pass
   - Don't worry about perfection yet
   - Run test → it should pass

3. **🔄 REFACTOR**: Improve code quality
   - Clean up implementation
   - Remove duplication
   - Improve naming
   - Run tests → should still pass

4. **📊 COVERAGE**: Check coverage
   - Run `pytest --cov=. --cov-report=html`
   - Identify untested code
   - Add tests for edge cases

### Step-by-Step Implementation Plan

### Step 1: Setup with Testing Infrastructure
1. Create virtual environment: `python3 -m venv venv`
2. Activate: `source venv/bin/activate`
3. Create `requirements.txt` and `requirements-dev.txt`
4. Install: `pip install -r requirements-dev.txt`
5. Create directory structure
6. Set up `pytest.ini`
7. Create `.gitignore`
8. Initial test run: `pytest` (should find 0 tests)

### Step 2: Core Mathematics (TDD Cycle)

**Feature: Rotation Calculation**
```python
# 1. 🔴 Write test first (tests/test_spirograph.py)
def test_calculate_required_rotations():
    assert calculate_required_rotations(105, 64) == 105
    assert calculate_required_rotations(96, 36) == 8
    assert calculate_required_rotations(100, 50) == 2

# 2. 🟢 Implement (spirograph.py)
import math

def calculate_required_rotations(R, r):
    """Calculate rotations needed to complete pattern."""
    return R // math.gcd(R, r)

# 3. 🔄 Run: pytest -v
# 4. ✅ All pass? Move to next feature
```

**Feature: Point Generation**
```python
# 1. 🔴 Write test
def test_hypocycloid_generates_points():
    points = generate_spirograph(
        fixed_teeth=96,
        moving_teeth=36,
        pen_offset=0.7,
        num_rotations=8
    )
    assert len(points) > 0
    assert all(isinstance(p, tuple) and len(p) == 2 for p in points)

# 2. 🟢 Implement generate_spirograph()
# 3. 🔄 Refactor
# 4. 📊 Check coverage
```

### Step 3: Configuration System (TDD)
1. Write schema validation tests
2. Implement JSON loading with jsonschema
3. Write auto-rotation tests
4. Implement GCD-based rotation calculation
5. Write edge case tests (invalid JSON, missing fields)
6. Handle edge cases with clear error messages

### Step 4: Web Viewer (TDD for API, Manual for UI)
1. Write API endpoint tests
   - Test `/api/configs` returns list
   - Test `/api/draw` with valid config
   - Test `/api/draw` with invalid config
2. Implement Flask routes
3. Run API tests: `pytest tests/test_app.py`
4. Build HTML5 Canvas renderer (manual testing in browser)
5. Integration tests for full workflow

### Step 5: Interpolation (TDD)
1. Write easing function tests (verify mathematical correctness)
   - Test linear(0) == 0, linear(1) == 1
   - Test ease_in_out is symmetric
2. Implement easing functions
3. Write interpolation logic tests
   - Test teeth interpolation
   - Test color interpolation (RGB)
4. Implement configuration interpolation
5. Test non-integer teeth handling
6. Coverage check

### Step 6: Morphing Interface
1. Write animation sequence tests
2. Implement morphing logic
3. Build UI (manual testing)
4. End-to-end integration tests
5. Final coverage report

---

## Testing Strategy

### Unit Tests
- **spirograph.py**:
  - Mathematical correctness (verify against known patterns)
  - Edge cases (zero offset, equal wheels, coprime teeth)
  - Non-integer teeth support

- **config.py**:
  - Schema validation
  - File loading (valid/invalid JSON)
  - Auto-rotation calculation
  - Default value handling

- **interpolator.py**:
  - Easing function correctness
  - Interpolation accuracy
  - Color transitions
  - Edge cases (same config, extreme values)

- **app.py**:
  - API endpoints
  - Response formats
  - Error handling
  - Request validation

### Property-Based Tests (using Hypothesis - Optional)
```python
from hypothesis import given
import hypothesis.strategies as st

@given(
    R=st.integers(min_value=10, max_value=200),
    r=st.integers(min_value=5, max_value=100)
)
def test_rotation_calculation_properties(R, r):
    """Test mathematical properties that should always hold."""
    rotations = calculate_required_rotations(R, r)

    # Property 1: Result should always be positive and <= R
    assert 0 < rotations <= R

    # Property 2: Pattern should complete exactly
    gcd = math.gcd(R, r)
    assert (rotations * gcd) == R

    # Property 3: Rotations should divide R evenly
    assert R % rotations == 0
```

### Integration Tests
- **Full Workflow**:
  - Load config → Generate points → Verify pattern completes
  - Interpolate configs → Generate intermediates → Verify smoothness
  - API request → Response → Render → Verify output

- **End-to-End**:
  - Load config file
  - Auto-calculate rotations
  - Generate complete pattern
  - Verify point count matches expected
  - Verify pattern closes properly

### Coverage Goals
- **Overall**: >90% code coverage
- **Core Math**: 100% coverage (critical for correctness)
- **Config System**: >95% coverage
- **Interpolator**: >90% coverage
- **API**: >85% coverage

### Running Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_spirograph.py

# Run specific test
pytest tests/test_spirograph.py::test_calculate_required_rotations

# Verbose output
pytest -v

# Stop on first failure
pytest -x

# Run only failed tests from last run
pytest --lf
```

---

## Mathematical Validation & Test Cases

### Known Spirograph Patterns (for validation)

1. **Classic Pattern**:
   - Fixed wheel: R=105 teeth
   - Moving wheel: r=64 teeth
   - GCD(105, 64) = 1
   - Required rotations: 105
   - Expected: Complex, non-repeating until 105 rotations

2. **Simple Flower**:
   - Fixed wheel: R=84 teeth
   - Moving wheel: r=21 teeth
   - GCD(84, 21) = 21
   - Required rotations: 4
   - Expected: 4-petaled flower pattern

3. **Star Pattern**:
   - Fixed wheel: R=100 teeth
   - Moving wheel: r=75 teeth
   - GCD(100, 75) = 25
   - Required rotations: 4
   - Expected: 4-pointed star

4. **Complex Pattern**:
   - Fixed wheel: R=144 teeth
   - Moving wheel: r=55 teeth
   - GCD(144, 55) = 1
   - Required rotations: 144
   - Expected: Very complex pattern

### Edge Cases to Test

1. **Equal Wheel Sizes** (R = r):
   - Should produce a circle (if pen_offset = 0)
   - Should produce a smaller circle offset (if pen_offset > 0)

2. **Coprime Wheels** (GCD = 1):
   - Pattern requires maximum rotations (R rotations)
   - Most complex patterns

3. **Perfect Divisor** (r divides R evenly):
   - Simple patterns
   - Few rotations needed
   - Example: R=100, r=25 → 4 rotations

4. **Pen Offset = 0**:
   - Should produce perfect circle
   - Radius = R - r (for hypocycloid)

5. **Pen Offset = Wheel Radius**:
   - Maximum extension
   - Most dramatic curves

6. **Non-Integer Teeth**:
   - teeth = 64.5, 37.2, etc.
   - Pattern may never complete
   - GCD undefined
   - Used during interpolation

7. **Very Small Wheels** (r << R):
   - Many lobes
   - Intricate patterns

8. **Nearly Equal Wheels** (R ≈ r):
   - Large, sweeping curves
   - Few lobes

---

## Development Commands Reference

### Virtual Environment
```bash
# Create
python3 -m venv venv

# Activate (Linux/Mac)
source venv/bin/activate

# Activate (Windows)
venv\Scripts\activate

# Deactivate
deactivate
```

### Dependencies
```bash
# Install all dependencies
pip install -r requirements-dev.txt

# Freeze current dependencies
pip freeze > requirements.txt

# Install production only
pip install -r requirements.txt
```

### Testing
```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=. --cov-report=html
open htmlcov/index.html  # View coverage report

# Run specific module tests
pytest tests/test_spirograph.py -v

# Run with output (see print statements)
pytest -s

# Run tests matching pattern
pytest -k "rotation"
```

### Running the Application
```bash
# Development server
python app.py

# Or with Flask command
export FLASK_APP=app.py
export FLASK_ENV=development
flask run

# Access at http://localhost:5000
```

---

## Future Enhancements (Post-MVP)

### Phase 3: Advanced Features
1. **Multiple Moving Wheels**:
   - Epicyclic gear trains
   - Complex nested patterns
   - 3+ wheel configurations

2. **3D Spirographs**:
   - Add z-axis rotation
   - Spherical spirographs
   - WebGL rendering

3. **Export Features**:
   - Save as SVG (vector)
   - Export animation as GIF
   - Export as MP4 video
   - Generate printable templates

4. **Advanced Interpolation**:
   - Bezier curve interpolation
   - Custom interpolation paths
   - Multi-config morphing (A→B→C→A)

5. **Audio Integration**:
   - Generate tones based on pattern
   - Frequency maps to teeth ratio
   - Musical spirographs

6. **Collaborative Features**:
   - Share configurations via URL
   - Gallery of user-created patterns
   - Pattern remix/variation generator

7. **Performance Optimizations**:
   - WebGL rendering for complex patterns
   - Web Workers for calculations
   - Caching of generated paths

8. **UI Enhancements**:
   - Real-time parameter sliders
   - Visual wheel representation
   - Undo/redo for config changes
   - Preset pattern library

---

## Success Criteria

### Phase 1 Complete When:
- [ ] All core tests passing (>90% coverage)
- [ ] Can load JSON config and render spirograph
- [ ] Auto-rotation calculation works correctly
- [ ] Web interface displays interactive visualization
- [ ] Can control animation speed and playback

### Phase 2 Complete When:
- [ ] Interpolation tests passing
- [ ] Can morph between two configurations
- [ ] Easing functions work correctly
- [ ] Non-integer teeth render properly
- [ ] Morphing animation is smooth

### Project Complete When:
- [ ] All tests passing with >90% coverage
- [ ] Documentation complete (README with examples)
- [ ] Example configurations provided
- [ ] Web interface is polished and responsive
- [ ] Can load, render, and animate spirographs
- [ ] Can interpolate and morph between patterns
- [ ] Code is well-documented and maintainable

---

## Notes & Considerations

### Mathematical Accuracy
- Use double precision for calculations
- Handle floating point errors gracefully
- Verify against known spirograph patterns
- Test with extreme values

### Performance
- Optimize point generation for large rotation counts
- Consider caching generated paths
- Use requestAnimationFrame for smooth animation
- Limit canvas size for performance

### User Experience
- Provide helpful error messages
- Show loading indicators for long calculations
- Allow cancellation of long animations
- Provide keyboard shortcuts (space = play/pause, etc.)

### Code Quality
- Follow PEP 8 style guide
- Use type hints where appropriate
- Write clear docstrings
- Keep functions small and focused
- Avoid premature optimization

---

## Resources & References

### Spirograph Mathematics
- [Spirograph Mathematics (Wikipedia)](https://en.wikipedia.org/wiki/Spirograph)
- [Parametric Equations for Epicycloids](https://mathworld.wolfram.com/Epicycloid.html)
- [Parametric Equations for Hypocycloids](https://mathworld.wolfram.com/Hypocycloid.html)

### Testing Resources
- [pytest Documentation](https://docs.pytest.org/)
- [Hypothesis Documentation](https://hypothesis.readthedocs.io/)
- [Test-Driven Development Guide](https://testdriven.io/)

### Web Development
- [Flask Documentation](https://flask.palletsprojects.com/)
- [HTML5 Canvas Tutorial](https://developer.mozilla.org/en-US/docs/Web/API/Canvas_API/Tutorial)
- [JSON Schema Validation](https://python-jsonschema.readthedocs.io/)

---

*This plan will be updated as the project evolves. All major changes should be documented here.*
