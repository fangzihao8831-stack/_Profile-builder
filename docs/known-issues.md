# Known Issues & Mitigations

## 1. Coordinate System Alignment

**Problem**: OCR/VLM coordinates are in image space, but PyAutoGUI needs screen space.

**Factors that break alignment**:
- Windows DPI scaling (100%, 125%, 150%)
- Browser window not at (0,0)
- Screenshot resized to 720p
- Multi-monitor setups

**Mitigation**:
```python
import ctypes

# Set DPI awareness at startup (Windows)
ctypes.windll.shcore.SetProcessDpiAwareness(2)

def image_to_screen(image_coords, screenshot_size, window_position):
    """
    Convert image coordinates to screen coordinates

    Args:
        image_coords: (x, y) from OCR/VLM (in 720p space)
        screenshot_size: Original screenshot dimensions
        window_position: (x, y) of browser window on screen
    """
    # Scale from 720p to original
    scale_x = screenshot_size[0] / 1280
    scale_y = screenshot_size[1] / 720

    screen_x = (image_coords[0] * scale_x) + window_position[0]
    screen_y = (image_coords[1] * scale_y) + window_position[1]

    return (int(screen_x), int(screen_y))
```

**Calibration test**: On first run, click a known element and verify visually.

---

## 2. VLM Coordinate Precision

**Problem**: Qwen2.5-VL might return coordinates that are close but not exactly on the button.

**Observed behavior**:
- Usually within 20-30px of correct location
- Sometimes returns center of wrong element
- Confidence varies

**Mitigation**:
1. Request bounding box, click center
2. Verify click success
3. If failed, retry with offset
4. Log failures for pattern analysis

```python
def click_with_retry(target, max_retries=3):
    bbox = find_element(target)
    center = get_center(bbox)

    for attempt in range(max_retries):
        result = verified_click(center)

        if result["success"]:
            return result

        # Try offset positions
        offsets = [(10, 0), (-10, 0), (0, 10), (0, -10)]
        if attempt < len(offsets):
            center = (center[0] + offsets[attempt][0],
                     center[1] + offsets[attempt][1])

    return {"success": False, "attempts": max_retries}
```

---

## 3. Memory Pressure

**Components in memory**:
| Component | RAM | VRAM |
|-----------|-----|------|
| AdsPower browser | ~500MB-1GB | varies |
| Qwen2.5-VL-7B | - | ~8-10GB |
| PaddleOCR | ~200MB | ~500MB |
| Python process | ~300MB | - |

**RTX 5080 16GB allocation**:
- Qwen2.5-VL: 10GB
- PaddleOCR: 0.5GB
- Available: 5.5GB (comfortable)

**Mitigation** (if memory issues arise):
```python
# Option 1: Unload OCR when not needed
paddle_ocr = None

def get_ocr():
    global paddle_ocr
    if paddle_ocr is None:
        paddle_ocr = PaddleOCR(use_gpu=True)
    return paddle_ocr

# Option 2: Use smaller Qwen model
# qwen2.5-vl:3b uses ~4GB VRAM
```

---

## 4. AdsPower Not Running

**Problem**: Script starts but AdsPower isn't running or profile doesn't exist.

**Error cases**:
- AdsPower not installed
- AdsPower not running
- Profile ID doesn't exist
- Profile already open elsewhere

**Mitigation**:
```python
def verify_adspower():
    try:
        resp = requests.get(f"{ADSPOWER_BASE}/status", timeout=2)
        return resp.status_code == 200
    except:
        return False

def startup_checks():
    if not verify_adspower():
        raise StartupError(
            "AdsPower not running. Please start AdsPower and try again."
        )

    if not profile_exists(PROFILE_ID):
        raise StartupError(
            f"Profile {PROFILE_ID} not found in AdsPower."
        )
```

---

## 5. Session Crash Recovery

**Problem**: Script crashes mid-session, browser left open, state lost.

**Consequences**:
- Orphaned browser consuming resources
- Lost session progress
- Potential detection (abandoned session)

**Mitigation**:
```python
import atexit
import signal

class Session:
    def __init__(self, profile_id):
        self.profile_id = profile_id
        self.checkpoint_file = f"data/sessions/{profile_id}_checkpoint.json"

        # Register cleanup handlers
        atexit.register(self.cleanup)
        signal.signal(signal.SIGINT, self.handle_interrupt)
        signal.signal(signal.SIGTERM, self.handle_interrupt)

    def save_checkpoint(self):
        checkpoint = {
            "timestamp": now(),
            "url": self.current_url,
            "actions_completed": self.action_count,
            "state": self.state
        }
        save_json(self.checkpoint_file, checkpoint)

    def cleanup(self):
        self.save_checkpoint()
        close_profile(self.profile_id)

    def handle_interrupt(self, sig, frame):
        print("\nInterrupted. Saving checkpoint...")
        self.cleanup()
        sys.exit(0)
```

**Orphan detection on startup**:
```python
def cleanup_orphans():
    """Close any browsers left from crashed sessions"""
    for checkpoint in glob("data/sessions/*_checkpoint.json"):
        profile_id = extract_profile_id(checkpoint)

        if is_profile_active(profile_id):
            print(f"Closing orphaned profile: {profile_id}")
            close_profile(profile_id)
```

---

## 6. Detection Over Time

**Problem**: Even with personas, patterns might emerge across many sessions.

**Detection vectors**:
- Too consistent timing between actions
- Same browsing paths repeated
- Unnatural session frequencies
- Missing typical user behaviors

**Mitigation**:
```python
def randomize_timing(base_seconds):
    """Add human-like variance to timing"""
    variance = random.uniform(0.7, 1.5)
    jitter = random.uniform(-0.2, 0.2)
    return base_seconds * variance + jitter

def should_take_break():
    """Occasionally pause like real humans"""
    if random.random() < 0.05:  # 5% chance
        return random.uniform(5, 30)  # 5-30 second break
    return 0
```

**Session frequency limits**:
- Max 3-4 sessions per profile per day
- Random gaps between sessions (1-4 hours)
- Vary session duration (15-60 min)
- Some days skip entirely
