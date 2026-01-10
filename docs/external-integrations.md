# External Integrations

## HumanCursor

**Repository**: [riflosnake/HumanCursor](https://github.com/riflosnake/HumanCursor)
**License**: MIT
**Purpose**: Human-like mouse movement with bezier curves

### What It Does
- Generates realistic mouse trajectories
- Uses bezier curves (not linear interpolation)
- Varies speed naturally (accelerate/decelerate)
- OS-level mouse control (works with any application)

### How We Use It
```python
from humancursor import SystemCursor

cursor = SystemCursor()

# Move to coordinates with human-like path
cursor.move_to([x, y])

# Click at current position
cursor.click()

# Move and click in one action
cursor.move_to([x, y])
cursor.click()
```

### Why Not Selenium?
- `element.click()` is instant (detectable)
- No mouse movement events fired
- Event listeners can detect synthetic events
- HumanCursor fires real OS events

---

## PaddleOCR

**Repository**: [PaddlePaddle/PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR)
**License**: Apache 2.0
**Purpose**: Fast text detection and recognition

### Role in Cascade
- First attempt for element finding (50-100ms)
- Finds text-based elements: buttons, links, labels
- Returns bounding box coordinates
- Falls back to VLM if text not found

### Setup
```bash
pip install paddleocr paddlepaddle-gpu
```

### How We Use It
```python
from paddleocr import PaddleOCR

ocr = PaddleOCR(use_gpu=True, show_log=False)

def find_text(screenshot, target_text):
    results = ocr.ocr(screenshot)

    for line in results[0]:
        bbox, (text, confidence) = line
        if target_text.lower() in text.lower() and confidence > 0.8:
            return {
                "bbox": bbox,  # [[x1,y1], [x2,y1], [x2,y2], [x1,y2]]
                "text": text,
                "confidence": confidence
            }

    return None
```

### Limitations
- Cannot find icons or images
- Cannot find elements without visible text
- May miss stylized/unusual fonts
- These cases fall back to VLM

---

## AdsPower

**Website**: [adspower.com](https://www.adspower.com/)
**Type**: Commercial anti-detect browser
**Purpose**: Fingerprint management and browser profiles

### What It Does
- Manages multiple browser profiles
- Each profile has unique fingerprint (canvas, WebGL, fonts, etc.)
- Profiles persist cookies and history
- Local API for automation

### API Endpoints
```python
ADSPOWER_BASE = "http://local.adspower.net:50325"

# Open browser profile
def open_profile(profile_id):
    resp = requests.get(
        f"{ADSPOWER_BASE}/api/v1/browser/start",
        params={"user_id": profile_id}
    )
    data = resp.json()

    if data["code"] == 0:
        return {
            "selenium_port": data["data"]["ws"]["selenium"],
            "debug_port": data["data"]["debug_port"]
        }
    raise Exception(f"Failed to open profile: {data}")

# Close browser profile
def close_profile(profile_id):
    requests.get(
        f"{ADSPOWER_BASE}/api/v1/browser/stop",
        params={"user_id": profile_id}
    )

# Check if profile is running
def is_profile_active(profile_id):
    resp = requests.get(
        f"{ADSPOWER_BASE}/api/v1/browser/active",
        params={"user_id": profile_id}
    )
    return resp.json()["data"]["status"] == "Active"
```

### Connecting Selenium (for screenshots only)
```python
from selenium import webdriver

def connect_to_profile(selenium_port):
    options = webdriver.ChromeOptions()
    options.debugger_address = f"127.0.0.1:{selenium_port}"

    driver = webdriver.Chrome(options=options)
    return driver
```

**Important**: We only use Selenium for:
- Taking screenshots
- Reading current URL
- Checking page load state

Never for clicking or typing!

---

## Ollama + Qwen2.5-VL-7B

**Ollama**: [ollama.com](https://ollama.com/)
**Model**: qwen2.5-vl:7b
**Purpose**: Vision-language model for decisions and element finding

### Setup
```bash
# Install Ollama
# Download from ollama.com

# Pull the model
ollama pull qwen2.5-vl:7b

# Verify
ollama list
```

### Configuration
```python
import ollama

def ask_vlm(image_path, prompt):
    response = ollama.chat(
        model="qwen2.5-vl:7b",
        messages=[{
            "role": "user",
            "content": prompt,
            "images": [image_path]
        }],
        options={
            "keep_alive": -1,  # Stay in VRAM
        },
        format="json"  # Structured output
    )

    return json.loads(response["message"]["content"])
```

### Memory Management
- `keep_alive: -1` keeps model loaded indefinitely
- Eliminates 5-10s cold start
- Uses ~8-10GB VRAM
- Combined with PaddleOCR (~500MB), fits in 16GB
