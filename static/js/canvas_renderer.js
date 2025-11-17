/**
 * Spirograph Canvas Renderer
 *
 * Interactive HTML5 Canvas visualization for spirograph patterns
 */

class SpirographRenderer {
    constructor(canvasId) {
        this.canvas = document.getElementById(canvasId);
        this.ctx = this.canvas.getContext('2d');

        // Animation state
        this.points = [];
        this.currentPoint = 0;
        this.isPlaying = false;
        this.speed = 1.0;
        this.animationId = null;
        this.showCompleteOnly = false;

        // Pattern metadata
        this.rotationCount = 0;
        this.currentRotation = 0;

        // Morphing state
        this.morphConfigs = [];
        this.morphIndex = 0;
        this.morphIntervalId = null;

        // Setup canvas
        this.resizeCanvas();
        window.addEventListener('resize', () => this.resizeCanvas());

        // Initialize controls
        this.initializeControls();

        // Load available configurations
        this.loadConfigurations();
    }

    resizeCanvas() {
        const container = this.canvas.parentElement;
        this.canvas.width = container.clientWidth;
        this.canvas.height = container.clientHeight;
        this.redraw();
    }

    initializeControls() {
        // Config selection
        document.getElementById('load-config-btn').addEventListener('click', () => {
            this.loadSelectedConfig();
        });

        // Animation controls
        document.getElementById('play-btn').addEventListener('click', () => {
            this.play();
        });

        document.getElementById('pause-btn').addEventListener('click', () => {
            this.pause();
        });

        document.getElementById('reset-btn').addEventListener('click', () => {
            this.reset();
        });

        document.getElementById('clear-btn').addEventListener('click', () => {
            this.clear();
        });

        // Speed control
        const speedSlider = document.getElementById('speed-slider');
        speedSlider.addEventListener('input', (e) => {
            this.speed = parseFloat(e.target.value);
            document.getElementById('speed-value').textContent = this.speed.toFixed(1) + 'x';
        });

        // Show complete only checkbox
        document.getElementById('show-complete-only').addEventListener('change', (e) => {
            this.showCompleteOnly = e.target.checked;
            if (this.showCompleteOnly && this.points.length > 0) {
                // If checked and we have points, show complete pattern immediately
                this.showCompletePattern();
            }
        });

        // Morph duration input
        const morphDuration = document.getElementById('morph-duration');
        morphDuration.addEventListener('input', (e) => {
            const duration = parseFloat(e.target.value);
            const steps = Math.round(duration * 24);
            document.getElementById('morph-steps-display').textContent = `${steps} frames`;
        });

        // Morph controls
        document.getElementById('morph-btn').addEventListener('click', () => {
            this.generateMorph();
        });

        document.getElementById('start-morph-btn').addEventListener('click', () => {
            this.playMorphSequence();
        });

        document.getElementById('export-video-btn').addEventListener('click', () => {
            this.exportVideo();
        });
    }

    async loadConfigurations() {
        try {
            const response = await fetch('/api/configs');
            const configs = await response.json();

            // Populate dropdowns
            const selectors = [
                'config-select',
                'morph-config-a',
                'morph-config-b'
            ];

            selectors.forEach(selectorId => {
                const select = document.getElementById(selectorId);
                configs.forEach(config => {
                    const option = document.createElement('option');
                    option.value = config.filename;
                    option.textContent = config.name;
                    select.appendChild(option);
                });
            });

        } catch (error) {
            console.error('Error loading configurations:', error);
        }
    }

    async loadSelectedConfig() {
        const select = document.getElementById('config-select');
        const filename = select.value;

        if (!filename) {
            alert('Please select a configuration');
            return;
        }

        try {
            const response = await fetch(`/api/config/${filename}`);
            const config = await response.json();

            await this.drawConfig(config);
        } catch (error) {
            console.error('Error loading config:', error);
            alert('Error loading configuration');
        }
    }

    async drawConfig(config) {
        try {
            const response = await fetch('/api/draw', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(config)
            });

            const data = await response.json();

            if (data.error) {
                alert(`Error: ${data.error}`);
                return;
            }

            this.points = data.points;
            this.rotationCount = data.rotation_count;
            this.currentPoint = 0;
            this.currentRotation = 0;

            this.updateInfo();

            // Show complete pattern immediately if checkbox is checked
            if (this.showCompleteOnly) {
                this.showCompletePattern();
            } else {
                this.reset();
            }

        } catch (error) {
            console.error('Error drawing spirograph:', error);
            alert('Error generating pattern');
        }
    }

    showCompletePattern() {
        this.clear();
        this.currentPoint = this.points.length - 1;
        this.currentRotation = this.rotationCount;

        // Draw all segments at once
        for (let i = 0; i < this.points.length - 1; i++) {
            this.drawSegment(i);
        }

        this.updateInfo();
    }

    async generateMorph() {
        const configAFilename = document.getElementById('morph-config-a').value;
        const configBFilename = document.getElementById('morph-config-b').value;
        const duration = parseFloat(document.getElementById('morph-duration').value);
        const easing = document.getElementById('easing-select').value;

        // Calculate steps based on duration at 24 fps
        const steps = Math.round(duration * 24);

        if (!configAFilename || !configBFilename) {
            alert('Please select both configurations');
            return;
        }

        try {
            // Hide animation controls and show progress
            document.getElementById('morph-animation-controls').style.display = 'none';
            document.getElementById('morph-progress-container').style.display = 'block';
            document.getElementById('morph-progress-bar').style.width = '0%';
            document.getElementById('morph-progress-text').textContent = `0 / ${steps}`;

            // Load both configs
            const [respA, respB] = await Promise.all([
                fetch(`/api/config/${configAFilename}`),
                fetch(`/api/config/${configBFilename}`)
            ]);

            const [configA, configB] = await Promise.all([
                respA.json(),
                respB.json()
            ]);

            // Generate interpolated configs
            const response = await fetch('/api/interpolate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    config_a: configA,
                    config_b: configB,
                    steps: steps,
                    easing: easing
                })
            });

            const data = await response.json();
            this.morphConfigs = data.configs;
            this.morphIndex = 0;

            console.log(`Morph: ${steps} frames over ${duration} seconds (24 fps)`);

            // Pre-generate all patterns with progress updates
            await this.preGenerateMorphPatterns();

            // Show animation controls when done
            document.getElementById('morph-progress-container').style.display = 'none';
            document.getElementById('morph-animation-controls').style.display = 'block';

            console.log('Generation complete! Ready to play or export.');

        } catch (error) {
            console.error('Error generating morph:', error);
            alert('Error generating morph animation');
            document.getElementById('morph-progress-container').style.display = 'none';
        }
    }

    async preGenerateMorphPatterns() {
        // Generate all patterns upfront
        console.log('Pre-generating patterns...');

        const total = this.morphConfigs.length;

        for (let i = 0; i < total; i++) {
            const config = this.morphConfigs[i];

            try {
                const response = await fetch('/api/draw', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(config)
                });

                const data = await response.json();

                // Store the points data in the config
                this.morphConfigs[i]._points = data.points;
                this.morphConfigs[i]._rotation_count = data.rotation_count;

                // Update progress bar
                const progress = ((i + 1) / total) * 100;
                document.getElementById('morph-progress-bar').style.width = `${progress}%`;
                document.getElementById('morph-progress-text').textContent = `${i + 1} / ${total}`;

                // Show progress in console
                if ((i + 1) % 10 === 0 || i === total - 1) {
                    console.log(`Generated ${i + 1}/${total} patterns`);
                }
            } catch (error) {
                console.error(`Error generating pattern ${i}:`, error);
            }
        }

        console.log('All patterns generated!');
    }

    playMorphSequence() {
        // Stop any existing morph animation
        if (this.morphIntervalId) {
            clearInterval(this.morphIntervalId);
        }

        this.morphIndex = 0;

        // Play at 24 fps = 1000ms / 24 ≈ 41.67ms per frame
        const frameInterval = 1000 / 24;

        this.morphIntervalId = setInterval(() => {
            if (this.morphIndex >= this.morphConfigs.length) {
                clearInterval(this.morphIntervalId);
                this.morphIntervalId = null;
                console.log('Morph sequence complete!');
                return;
            }

            // Display the complete pattern for this frame
            this.displayMorphFrame(this.morphIndex);
            this.morphIndex++;
        }, frameInterval);

        console.log('Playing morph sequence at 24 fps...');
    }

    displayMorphFrame(index) {
        if (index >= this.morphConfigs.length) return;

        const config = this.morphConfigs[index];

        if (!config._points) {
            console.error('Pattern not pre-generated for frame', index);
            return;
        }

        // Set the points and draw complete pattern
        this.points = config._points;
        this.rotationCount = config._rotation_count;
        this.currentPoint = this.points.length - 1;
        this.currentRotation = this.rotationCount;

        // Draw the complete pattern
        this.clear();
        for (let i = 0; i < this.points.length - 1; i++) {
            this.drawSegment(i);
        }

        this.updateInfo();
    }

    play() {
        if (this.isPlaying) return;

        // If showCompleteOnly is checked, just display complete pattern
        if (this.showCompleteOnly) {
            this.showCompletePattern();
            return;
        }

        this.isPlaying = true;
        this.animate();
    }

    pause() {
        this.isPlaying = false;
        if (this.animationId) {
            cancelAnimationFrame(this.animationId);
        }
        // Also stop morph sequence if playing
        if (this.morphIntervalId) {
            clearInterval(this.morphIntervalId);
            this.morphIntervalId = null;
        }
    }

    reset() {
        this.pause();
        this.currentPoint = 0;
        this.currentRotation = 0;
        this.clear();
        this.updateInfo();
    }

    clear() {
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
    }

    animate() {
        if (!this.isPlaying) return;

        const pointsPerFrame = Math.max(1, Math.floor(this.speed));

        for (let i = 0; i < pointsPerFrame; i++) {
            if (this.currentPoint >= this.points.length - 1) {
                this.pause();
                return;
            }

            this.drawSegment(this.currentPoint);
            this.currentPoint++;

            // Update rotation count
            const pointsPerRotation = this.points.length / this.rotationCount;
            this.currentRotation = Math.floor(this.currentPoint / pointsPerRotation);
        }

        this.updateInfo();
        this.animationId = requestAnimationFrame(() => this.animate());
    }

    drawSegment(index) {
        if (index >= this.points.length - 1) return;

        const [x1, y1] = this.points[index];
        const [x2, y2] = this.points[index + 1];

        // Transform to canvas coordinates
        const centerX = this.canvas.width / 2;
        const centerY = this.canvas.height / 2;
        const scale = Math.min(this.canvas.width, this.canvas.height) * 0.4;

        this.ctx.strokeStyle = '#2E86AB';
        this.ctx.lineWidth = 2;
        this.ctx.lineCap = 'round';

        this.ctx.beginPath();
        this.ctx.moveTo(centerX + x1 * scale, centerY + y1 * scale);
        this.ctx.lineTo(centerX + x2 * scale, centerY + y2 * scale);
        this.ctx.stroke();
    }

    redraw() {
        this.clear();
        for (let i = 0; i < this.currentPoint; i++) {
            this.drawSegment(i);
        }
    }

    async exportVideo() {
        if (!this.morphConfigs || this.morphConfigs.length === 0) {
            alert('Please generate a morph first');
            return;
        }

        try {
            // Check if MediaRecorder is supported
            if (!window.MediaRecorder) {
                alert('Video recording is not supported in your browser. Please use Chrome, Firefox, or Edge.');
                return;
            }

            // Show recording status
            document.getElementById('recording-status').style.display = 'block';

            // Create video stream from canvas
            const stream = this.canvas.captureStream(24); // 24 fps
            const mediaRecorder = new MediaRecorder(stream, {
                mimeType: 'video/webm;codecs=vp9',
                videoBitsPerSecond: 5000000 // 5 Mbps
            });

            const chunks = [];

            mediaRecorder.ondataavailable = (e) => {
                if (e.data.size > 0) {
                    chunks.push(e.data);
                }
            };

            mediaRecorder.onstop = () => {
                // Create blob and download
                const blob = new Blob(chunks, { type: 'video/webm' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `spirograph-morph-${Date.now()}.webm`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                URL.revokeObjectURL(url);

                // Hide recording status
                document.getElementById('recording-status').style.display = 'none';

                console.log('Video exported successfully!');
            };

            // Start recording
            mediaRecorder.start();

            // Play the morph sequence
            this.morphIndex = 0;
            const frameInterval = 1000 / 24;

            await new Promise((resolve) => {
                const recordInterval = setInterval(() => {
                    if (this.morphIndex >= this.morphConfigs.length) {
                        clearInterval(recordInterval);
                        // Stop recording after a small delay
                        setTimeout(() => {
                            mediaRecorder.stop();
                            resolve();
                        }, 100);
                        return;
                    }

                    this.displayMorphFrame(this.morphIndex);
                    this.morphIndex++;
                }, frameInterval);
            });

        } catch (error) {
            console.error('Error exporting video:', error);
            alert('Error exporting video: ' + error.message);
            document.getElementById('recording-status').style.display = 'none';
        }
    }

    updateInfo() {
        document.getElementById('current-rotation').textContent = this.currentRotation;
        document.getElementById('total-rotations').textContent = this.rotationCount;
        document.getElementById('point-count').textContent = this.points.length;
    }
}

// Initialize when page loads
document.addEventListener('DOMContentLoaded', () => {
    const renderer = new SpirographRenderer('spirograph-canvas');
});
