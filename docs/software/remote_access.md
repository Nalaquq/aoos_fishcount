# Remote Access & Camera Control

This document covers remote camera control capabilities for the AOOS Fish Count system, including the web-based camera control interface and contributing guidelines for making changes.

## Overview

The camera control system provides a Flask-based web interface for remote management of RPi camera capture operations. This enables operators to:

- **Remotely start/stop continuous image capture** from a browser on any machine on the network
- **Monitor capture status in real-time** with frame counts and timestamps
- **View camera state** (ready, active, stopped, error) with visual feedback
- **Access the system** from any networked device (no authentication required)

## Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                  Frontend (Browser)                         │
│  ┌─────────────────────────────────────────────────────┐   │
│  │     index.html - Single Page Application             │   │
│  │  - Status display badge                             │   │
│  │  - Start/Stop capture buttons                        │   │
│  │  - Real-time frame count & timestamps               │   │
│  │  - Auto-polling status (2s intervals)               │   │
│  └─────────────────────────────────────────────────────┘   │
│                           ↑ HTTP                            │
│                           ↓                                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │     Network Connection (any machine)                │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                           ↑ HTTP
                           ↓
┌─────────────────────────────────────────────────────────────┐
│                  Backend (RPi5)                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │     Flask Application                               │   │
│  │  ├─ /api/status    (GET)  - Camera state            │   │
│  │  ├─ /api/start     (POST) - Begin capture           │   │
│  │  └─ /api/stop      (POST) - End capture             │   │
│  └─────────────────────────────────────────────────────┘   │
│                           ↓                                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │     Capture Thread (Background)                     │   │
│  │  - Reads frames from USB camera via OpenCV         │   │
│  │  - Saves images with timestamps                    │   │
│  │  - Updates capture state                           │   │
│  └─────────────────────────────────────────────────────┘   │
│                           ↓                                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │     Camera Module                                   │   │
│  │  (aoos_fishcount.sensors.camera)                   │   │
│  │  - OpenCV frame capture                            │   │
│  │  - Exposure/white balance control                  │   │
│  └─────────────────────────────────────────────────────┘   │
│                           ↓                                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │     Storage                                         │   │
│  │  - data/captures/ - Timestamped JPEG images        │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## Quick Start

### Installation

1. **Install Flask dependency:**
   ```bash
   pip install -r requirements.txt
   ```
   Flask 3.0.0+ is required (automatically installed via `requirements.txt`)

2. **Verify camera module exists:**
   ```bash
   python -c "from aoos_fishcount.sensors.camera import CameraCapture; print('Camera module found')"
   ```

### Running the Application

**On the RPi5 (or any machine running the application):**

```bash
cd /path/to/aoos_fishcount
python -m camera_control_UI.camera_control
```

Output:
```
 * Running on http://0.0.0.0:5000
 * WARNING: This is a development server. Do not use it in production.
```

**From a client machine on the same network:**

Open a browser and navigate to:
```
http://<rpi-ip-address>:5000
```

Example: `http://192.168.1.100:5000`

### Usage

1. **Open the web interface** in your browser
2. **Check camera status** - The status badge displays one of:
   - 🟢 **Ready** - Camera initialized, waiting for commands
   - 🔵 **Active** - Currently capturing frames (pulsing indicator)
   - 🟡 **Stopped** - Capture was halted
   - 🔴 **Error** - Something went wrong (check error message)

3. **Start capturing:**
   - Click the "▶ Start Capturing" button
   - Status changes to "Active"
   - Frame counter increments in real-time
   - Last capture timestamp updates continuously

4. **Stop capturing:**
   - Click the "⏹ Stop Capturing" button
   - Background capture thread terminates gracefully
   - Status changes to "Ready"

5. **View captured images:**
   - Images are saved to `data/captures/` on the RPi
   - Filenames follow format: `capture_YYYYMMDD_HHMMSS_mmm.jpg`
   - Example: `capture_20260421_143025_123.jpg`

## API Reference

### GET `/api/status`

Returns the current camera state and capture statistics.

**Response:**
```json
{
  "status": "active",
  "capture_count": 245,
  "last_capture_time": "2026-04-21T14:30:25.123456",
  "error_message": null,
  "capturing": true
}
```

| Field | Type | Description |
|-------|------|-------------|
| `status` | string | One of: `ready`, `active`, `stopped`, `error` |
| `capture_count` | integer | Number of frames captured in current session |
| `last_capture_time` | string (ISO8601) | Timestamp of most recent frame, or `null` |
| `error_message` | string or null | Error details if status is `error` |
| `capturing` | boolean | Whether capture thread is running |

---

### POST `/api/start`

Start continuous frame capture in a background thread.

**Request Body:** (empty)

**Response:**
```json
{
  "success": true,
  "message": "Capture started"
}
```

**Error Response:**
```json
{
  "success": false,
  "message": "Capture already running"
}
```

**Possible Errors:**
- `"Capture already running"` - Capture is already active
- `"Camera not initialized"` - Camera failed to initialize on startup

---

### POST `/api/stop`

Stop the background capture thread gracefully.

**Request Body:** (empty)

**Response:**
```json
{
  "success": true,
  "message": "Capture stopped"
}
```

**Error Response:**
```json
{
  "success": false,
  "message": "Capture not running"
}
```

## Use Cases

### 1. Field Monitoring
Set up a basic laptop/tablet at the field site to monitor and control the RPi-based camera system without needing to physically access the device.

### 2. Remote Activation
Start capture from an office machine, then let the system run continuously while collecting data.

### 3. Multi-Site Coordination
If multiple RPi systems are deployed, maintain separate browser tabs for each one and coordinate captures across sites.

### 4. Troubleshooting
Check real-time capture status and error messages to diagnose camera or hardware issues remotely.

## Configuration

### Camera Settings

To modify camera capture parameters (resolution, FPS, exposure), edit the initialization in `camera_control.py`:

```python
def initialize_camera(config: dict | None = None) -> bool:
    """Initialize the camera with optional config."""
    camera_config = {
        "device_index": 0,      # USB camera index (usually 0)
        "width": 1920,          # Frame width in pixels
        "height": 1080,         # Frame height in pixels
        "fps": 30,              # Frames per second
    }
```

Advanced exposure settings can be passed via the `exposure` parameter. See `aoos_fishcount.sensors.camera.CameraCapture` for details.

### Storage Location

Images are saved to `data/captures/` by default. To change:

```python
captures_dir = project_root / "data" / "captures"  # Configure here
```

### Network Binding

The Flask app binds to `0.0.0.0:5000` (all interfaces). To restrict to localhost only:

```python
# In camera_control.py, main section:
app.run(host="127.0.0.1", port=5000)  # Only local access
```

To use a different port:

```python
app.run(host="0.0.0.0", port=8000)  # Use port 8000 instead
```

## Contributing

### For Developers: Making Changes

This section explains how to safely modify the camera control system.

#### 1. **Code Structure & Responsibilities**

The system is split into clear responsibilities:

| Component | File | Purpose |
|-----------|------|---------|
| Backend API | `camera_control_UI/camera_control.py` | Flask routes, thread management, camera initialization |
| Frontend UI | `camera_control_UI/index.html` | HTML, CSS, JavaScript, status polling |
| Camera Driver | `aoos_fishcount/sensors/camera.py` | OpenCV capture, exposure control (do not modify for camera control feature) |

**Rule:** Changes should be confined to the appropriate module. For example:
- UI changes → modify `index.html`
- API logic changes → modify `camera_control.py`
- Do NOT modify `camera.py` unless coordinating with fish counting pipeline

---

#### 2. **Adding New API Endpoints**

If you need new functionality (e.g., capture settings, image preview):

**Step 1:** Define the route in `camera_control.py`:
```python
@app.route("/api/settings", methods=["GET", "POST"])
def api_settings():
    """Get or update camera settings."""
    if request.method == "GET":
        # Return current settings
        return jsonify({"width": 1920, "height": 1080, ...})
    else:
        # Update settings
        data = request.json
        # Validate and apply changes
        return jsonify({"success": True})
```

**Step 2:** Add corresponding frontend button/form in `index.html`

**Step 3:** Implement JavaScript handler:
```javascript
async function updateSettings(setting, value) {
    const response = await fetch("/api/settings", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({setting: setting, value: value})
    });
    // Handle response
}
```

**Step 4:** Test with curl or Postman:
```bash
curl -X POST http://localhost:5000/api/settings \
  -H "Content-Type: application/json" \
  -d '{"width": 2560}'
```

---

#### 3. **Modifying the Frontend UI**

When updating `index.html`:

**Keep in mind:**
- The status polling interval is 2 seconds. Don't reduce below 1s (load concerns)
- Button states are managed by `isCapturing` flag. Keep them in sync
- Use the existing `showMessage()` function for user feedback
- Maintain responsive design for mobile browsers

**Example: Adding a setting control**
```html
<div class="settings-section">
    <label>Capture FPS</label>
    <input type="number" id="fpsInput" min="1" max="60" value="30">
    <button onclick="applyFPS()">Apply</button>
</div>
```

Then add JavaScript:
```javascript
async function applyFPS() {
    const fps = document.getElementById("fpsInput").value;
    const response = await fetch("/api/settings", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({fps: parseInt(fps)})
    });
    const data = await response.json();
    showMessage(data.success ? "FPS updated" : "Failed", 
                data.success ? "success" : "error");
}
```

---

#### 4. **Thread Safety & State Management**

The capture system uses background threading. **Important rules:**

- **Always use `capture_thread_lock`** when reading/writing `camera_state`:
  ```python
  with capture_thread_lock:
      camera_state["capture_count"] += 1
  ```

- **Don't block the Flask thread** with long operations:
  ```python
  # ❌ Wrong - blocks Flask
  for i in range(1000000):
      process_frame()
  
  # ✅ Correct - use threading for background work
  def background_worker():
      for i in range(1000000):
          process_frame()
  thread = threading.Thread(target=background_worker, daemon=True)
  thread.start()
  ```

- **Always provide graceful shutdown** (set `capture_running = False` rather than forcing thread termination)

---

#### 5. **Testing Your Changes**

**Local Testing (without RPi):**
```bash
# Install dependencies
pip install Flask opencv-python numpy

# Run the app
python -m camera_control_UI.camera_control

# In another terminal, test endpoints
curl http://localhost:5000/api/status
curl -X POST http://localhost:5000/api/start
```

**Frontend Testing:**
- Test in different browsers (Chrome, Firefox, Safari, Edge)
- Test on mobile devices
- Open browser DevTools (F12) to check for JavaScript errors

**Hardware Testing (on RPi):**
```bash
# SSH to RPi
ssh pi@<rpi-ip>

# Run the app
cd ~/aoos_fishcount
python -m camera_control_UI.camera_control

# From another machine
curl http://<rpi-ip>:5000/api/status
```

---

#### 6. **Common Tasks & Code Patterns**

**Task: Add a reset button that clears capture count**
```python
@app.route("/api/reset", methods=["POST"])
def api_reset():
    with capture_thread_lock:
        camera_state["capture_count"] = 0
        camera_state["last_capture_time"] = None
    return jsonify({"success": True})
```

**Task: Add image preview endpoint**
```python
@app.route("/api/latest-image", methods=["GET"])
def api_latest_image():
    captures = sorted(get_captures_directory().glob("*.jpg"))
    if captures:
        return send_file(str(captures[-1]))
    else:
        abort(404)
```

**Task: Log capture statistics**
```python
# In capture_frames_worker():
if frame_count % 100 == 0:
    log.info(f"Captured {frame_count} frames, last: {filename}")
```

---

#### 7. **Code Style & Guidelines**

- **Python:** Follow PEP 8 (4-space indentation, snake_case for functions)
- **JavaScript:** Use camelCase, arrow functions, async/await
- **Comments:** Explain *why*, not *what* (code should be clear)
- **Error handling:** Provide meaningful error messages for debugging

**Example:**
```python
# ❌ Unclear
frame = camera.read()

# ✅ Clear with context
frame = camera.read()
if frame is None:
    log.warning("Frame read failed — check camera connection")
    continue
```

---

#### 8. **Backward Compatibility**

When modifying the system:

- **Don't break existing API contracts** - If `/api/status` returns `{"status": "..."}`, keep it in future versions
- **Add new fields conditionally** - Don't remove fields that clients may depend on
- **Version new endpoints** - If making breaking changes, use `/api/v2/endpoint`

---

#### 9. **Performance Considerations**

- **Capture loop:** Keep the 50ms delay to prevent CPU overhead
- **Status polling:** 2-second intervals balance responsiveness with network load
- **Frame saving:** 50MB+ per minute at 1920x1080 JPEG. Monitor disk space
- **Memory:** Background thread uses ~10-20MB. Safe for RPi5

---

#### 10. **Debugging**

Enable verbose logging in `camera_control.py`:
```python
logging.basicConfig(level=logging.DEBUG)  # Change INFO to DEBUG
```

Check logs:
```bash
# Live logs
tail -f data/logs/app.log

# Search for errors
grep "ERROR" data/logs/app.log
```

Browser console (F12):
- Check for JavaScript errors
- Monitor Network tab for failed API requests
- Use console for manual API calls: `fetch('/api/status').then(r => r.json()).then(console.log)`

---

### Submitting Changes

Before submitting changes or pull requests:

1. **Test thoroughly** - Unit test new functions, integration test the workflow
2. **Update documentation** - If adding features, document them here
3. **Follow code style** - Use existing patterns in the codebase
4. **Keep commits small** - One feature per commit
5. **Write clear commit messages** - Describe what changed and why

## Troubleshooting

### Application won't start
- **Check Flask is installed:** `pip list | grep Flask`
- **Check Python version:** `python --version` (3.9+ required)
- **Check port 5000 is free:** `netstat -an | grep 5000`

### Camera not initializing
- **Verify camera is connected:** `ls /dev/video*` (on RPi)
- **Check permissions:** Camera device may need read/write permissions
- **Try manual test:** 
  ```python
  from aoos_fishcount.sensors.camera import CameraCapture
  cam = CameraCapture(device_index=0)
  frame = cam.read()
  print(frame.shape)
  ```

### Images not saving
- **Check directory permissions:** `ls -la data/captures/`
- **Check disk space:** `df -h` (ensure /home partition has space)
- **Verify path:** Images always go to `data/captures/` relative to project root

### Frontend not updating status
- **Check browser console for errors (F12)**
- **Check API is responding:**
  ```bash
  curl http://localhost:5000/api/status
  ```
- **Check polling interval:** Look for "TypeError" in console, may indicate API down

### High CPU usage
- **Increase capture loop delay** from 50ms to 100ms+ in `camera_control.py`
- **Reduce polling interval** from 2000ms in `index.html` (but not below 1000ms)
- **Check for infinite loops** in JavaScript console

## See Also

- [Camera Module Documentation](../hardware/environmental_sensor.md) - Hardware sensor info
- [Configuration Guide](./configuration.md) - System configuration
- [Installation Guide](./installation.md) - Full setup instructions
