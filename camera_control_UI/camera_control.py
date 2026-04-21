"""
Flask application for RPi camera control UI.

Provides REST API endpoints to start/stop continuous image capture
from an RPi camera, and a web UI for remote control.
"""

import json
import logging
import os
import sys
import threading
import time
from datetime import datetime
from pathlib import Path

from flask import Flask, jsonify, render_template

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from aoos_fishcount.sensors.camera import CameraCapture

# Configure logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

# Global state
camera_state = {
    "status": "ready",  # ready, active, stopped, error
    "capture_count": 0,
    "last_capture_time": None,
    "error_message": None,
}
capture_thread = None
capture_thread_lock = threading.Lock()
capture_running = False
camera = None
captures_dir = None


def get_captures_directory() -> Path:
    """Get or create the captures directory."""
    global captures_dir
    if captures_dir is None:
        # Use data/captures directory relative to project root
        project_root = Path(__file__).parent.parent.parent
        captures_dir = project_root / "data" / "captures"
        captures_dir.mkdir(parents=True, exist_ok=True)
        log.info(f"Captures directory: {captures_dir}")
    return captures_dir


def initialize_camera(config: dict | None = None) -> bool:
    """Initialize the camera with optional config."""
    global camera
    try:
        # Default config
        camera_config = {
            "device_index": 0,
            "width": 1920,
            "height": 1080,
            "fps": 30,
        }
        if config:
            camera_config.update(config)

        camera = CameraCapture(**camera_config)
        log.info("Camera initialized successfully")
        return True
    except Exception as e:
        log.error(f"Failed to initialize camera: {e}")
        camera_state["status"] = "error"
        camera_state["error_message"] = str(e)
        return False


def capture_frames_worker() -> None:
    """Background worker thread that continuously captures frames."""
    global capture_running, camera_state
    
    log.info("Capture worker thread started")
    frame_count = 0
    
    while capture_running:
        try:
            # Read frame from camera
            frame = camera.read()
            if frame is None:
                log.warning("Frame read returned None")
                continue

            # Save frame with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
            filename = f"capture_{timestamp}.jpg"
            filepath = get_captures_directory() / filename

            # Write frame using cv2
            import cv2
            success = cv2.imwrite(str(filepath), frame)
            if success:
                frame_count += 1
                with capture_thread_lock:
                    camera_state["capture_count"] = frame_count
                    camera_state["last_capture_time"] = datetime.now().isoformat()
                log.debug(f"Saved: {filename}")
            else:
                log.error(f"Failed to write frame: {filepath}")

            # Small delay to avoid overwhelming the system
            time.sleep(0.05)

        except Exception as e:
            log.error(f"Error in capture worker: {e}")
            with capture_thread_lock:
                camera_state["status"] = "error"
                camera_state["error_message"] = str(e)
            break

    log.info(f"Capture worker thread stopped. Captured {frame_count} frames")


def start_capture() -> dict:
    """Start continuous frame capture in background thread."""
    global capture_thread, capture_running, camera_state

    with capture_thread_lock:
        if capture_running:
            return {"success": False, "message": "Capture already running"}

        if camera is None:
            return {"success": False, "message": "Camera not initialized"}

        # Reset counters
        camera_state["capture_count"] = 0
        camera_state["last_capture_time"] = None
        camera_state["status"] = "active"
        camera_state["error_message"] = None

        # Start background thread
        capture_running = True
        capture_thread = threading.Thread(target=capture_frames_worker, daemon=True)
        capture_thread.start()

    log.info("Capture started")
    return {"success": True, "message": "Capture started"}


def stop_capture() -> dict:
    """Stop the capture thread."""
    global capture_running, capture_thread

    with capture_thread_lock:
        if not capture_running:
            return {"success": False, "message": "Capture not running"}

        capture_running = False

    # Wait for thread to finish (with timeout)
    if capture_thread and capture_thread.is_alive():
        capture_thread.join(timeout=2.0)

    camera_state["status"] = "ready"
    log.info("Capture stopped")
    return {"success": True, "message": "Capture stopped"}


def create_app() -> Flask:
    """Create and configure the Flask app."""
    app = Flask(
        __name__,
        template_folder=Path(__file__).parent,
        static_folder=str(Path(__file__).parent / "static"),
    )

    # Initialize camera on startup
    @app.before_request
    def before_request():
        global camera
        if camera is None:
            initialize_camera()

    # API Routes
    @app.route("/api/status", methods=["GET"])
    def api_status():
        """Get current camera status and statistics."""
        with capture_thread_lock:
            return jsonify(
                {
                    "status": camera_state["status"],
                    "capture_count": camera_state["capture_count"],
                    "last_capture_time": camera_state["last_capture_time"],
                    "error_message": camera_state["error_message"],
                    "capturing": capture_running,
                }
            )

    @app.route("/api/start", methods=["POST"])
    def api_start():
        """Start capturing frames."""
        result = start_capture()
        status_code = 200 if result["success"] else 400
        return jsonify(result), status_code

    @app.route("/api/stop", methods=["POST"])
    def api_stop():
        """Stop capturing frames."""
        result = stop_capture()
        status_code = 200 if result["success"] else 400
        return jsonify(result), status_code

    # Web Routes
    @app.route("/", methods=["GET"])
    def index():
        """Serve the main UI page."""
        return render_template("index.html")

    @app.teardown_appcontext
    def cleanup(exception=None):
        """Clean up resources on app shutdown."""
        global camera
        if camera:
            try:
                stop_capture()
                camera.release()
                log.info("Camera released")
            except Exception as e:
                log.error(f"Error during cleanup: {e}")

    return app


if __name__ == "__main__":
    app = create_app()
    # Run on 0.0.0.0 to be accessible from other machines on the network
    app.run(host="0.0.0.0", port=5000, debug=False, threaded=True)
