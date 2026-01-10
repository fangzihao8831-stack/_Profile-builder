# Technical Decisions

## Why Top-Down Instead of Bottom-Up

**Bottom-up approach (rejected)**:
1. Build OCR first (fast)
2. Build CSS selectors
3. Add VLM as fallback

**Problem**: If OCR fails and CSS doesn't match, we hope VLM works. But VLM was never tested first.

**Top-down approach (chosen)**:
1. Build VLM first (reliable baseline)
2. Add OCR as optimization (tested against VLM)
3. Add CSS as further optimization

**Benefit**: VLM is proven to work before we optimize. Each faster layer is validated against the baseline. If fast layers fail, we have a tested fallback.

---

## Why Bounding Box Over Single Point

**Single point**:
```json
{"x": 450, "y": 320}
```
- Risk: Point might be at edge of button
- Risk: VLM estimation might be off by 20-30px
- No way to validate if point is inside element

**Bounding box**:
```json
{"x1": 400, "y1": 300, "x2": 500, "y2": 340}
```
- Click center of box = safer
- Can validate box size is reasonable
- Can retry with offset if center fails
- Only ~10 extra tokens (~50ms slower)

---

## Why Structured JSON Over Natural Language

**Natural language response**:
```
"The Add to Cart button is located in the center-right portion of the
screen, approximately 450 pixels from the left edge and 320 pixels
from the top."
```
- ~50 tokens
- Requires NLP parsing
- Ambiguous format
- Error-prone extraction

**Structured JSON response**:
```json
{"action": "click", "target": "Add to Cart", "x": 450, "y": 320}
```
- ~20 tokens (faster generation)
- Direct parsing with json.loads()
- Unambiguous format
- Easy validation

**Ollama setting**: `format: "json"` enforces JSON output.

---

## Qwen2.5-VL-7B Setup

### Model Configuration
```python
# Ollama API call
response = ollama.chat(
    model="qwen2.5-vl:7b",
    messages=[...],
    options={
        "keep_alive": -1,  # Keep in VRAM indefinitely
    },
    format="json"  # Enforce structured output
)
```

### keep_alive Parameter
- `-1` = keep model loaded forever (until Ollama restarts)
- Eliminates cold start latency (~5-10 seconds)
- Model stays in VRAM between calls
- Critical for responsive browsing

### Screenshot Preprocessing
```python
from PIL import Image

def prepare_screenshot(image_path):
    img = Image.open(image_path)

    # Resize to 720p (1280x720) for VLM
    # Maintains aspect ratio, reduces token count
    img = img.resize((1280, 720), Image.LANCZOS)

    # Store original dimensions for coordinate mapping
    original_size = (1920, 1080)  # example

    return img, original_size
```

### Coordinate Mapping
```python
def map_coordinates(vlm_coords, original_size, vlm_size=(1280, 720)):
    """Map VLM coordinates back to original screen space"""
    scale_x = original_size[0] / vlm_size[0]
    scale_y = original_size[1] / vlm_size[1]

    return {
        "x": int(vlm_coords["x"] * scale_x),
        "y": int(vlm_coords["y"] * scale_y)
    }
```

### Memory Usage (RTX 5080 16GB)
| Component | VRAM |
|-----------|------|
| Qwen2.5-VL-7B | ~8-10 GB |
| PaddleOCR | ~500 MB |
| Available | ~5-7 GB |

Both models fit comfortably with headroom.

---

## Dual-Purpose Verification

Same code path serves TWO purposes:

### Production Mode
```python
def find_element(target, mode="production"):
    # Always try fast methods first
    ocr_result = paddle_ocr.find(target)

    if ocr_result:
        return ocr_result  # Fast path

    # Fallback to VLM
    vlm_result = vision_llm.find(target)
    return vlm_result
```

### Testing Mode
```python
def find_element(target, mode="testing"):
    # Run ALL methods for comparison
    ocr_result = paddle_ocr.find(target)
    vlm_result = vision_llm.find(target)

    # Log accuracy metrics
    logger.info({
        "target": target,
        "ocr_found": ocr_result is not None,
        "vlm_found": vlm_result is not None,
        "match": is_close(ocr_result, vlm_result),
        "distance": calculate_distance(ocr_result, vlm_result)
    })

    return {
        "ocr": ocr_result,
        "vlm": vlm_result,
        "accuracy": calculate_accuracy(ocr_result, vlm_result)
    }
```

### Benefits
- Test suite uses real production code
- Accuracy metrics collected continuously
- No "test mode that works but production fails"
- Can run shadow mode (use fast, log comparison)
