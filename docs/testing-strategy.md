# Testing Strategy

## Philosophy

**VLM is ground truth.** All faster methods are tested against VLM accuracy.

## VLM as Ground Truth Baseline

Vision LLM (Qwen2.5-VL-7B) is:
- Slow (~500-2000ms)
- But reliable (can find any visual element)
- Our accuracy baseline

Before optimizing with OCR/CSS, VLM must work correctly.

## OCR Accuracy Comparison

### Offline Testing
```python
# tests/test_element_accuracy.py

TEST_SET = [
    {"screenshot": "google_search.png", "targets": ["Google Search", "I'm Feeling Lucky"]},
    {"screenshot": "amazon_product.png", "targets": ["Add to Cart", "Buy Now"]},
    {"screenshot": "cookie_banner.png", "targets": ["Accept", "Accept All", "Reject"]},
]

def test_ocr_accuracy():
    results = []

    for test in TEST_SET:
        screenshot = load_image(test["screenshot"])

        for target in test["targets"]:
            vlm_bbox = vision_llm.find(screenshot, target)
            ocr_bbox = paddle_ocr.find(screenshot, target)

            results.append({
                "screenshot": test["screenshot"],
                "target": target,
                "vlm_found": vlm_bbox is not None,
                "ocr_found": ocr_bbox is not None,
                "iou": calculate_iou(vlm_bbox, ocr_bbox),  # Intersection over Union
                "center_distance": calculate_distance(vlm_bbox, ocr_bbox)
            })

    # Report
    ocr_found_rate = sum(r["ocr_found"] for r in results) / len(results)
    avg_iou = sum(r["iou"] for r in results if r["iou"]) / len([r for r in results if r["iou"]])

    print(f"OCR detection rate: {ocr_found_rate:.1%}")
    print(f"Average IoU with VLM: {avg_iou:.2f}")

    assert ocr_found_rate >= 0.80, "OCR must find 80%+ of elements"
    assert avg_iou >= 0.70, "OCR boxes must overlap 70%+ with VLM"
```

### Runtime Logging
```python
# Continuous accuracy tracking during real sessions

def find_element_with_logging(target):
    vlm_result = vision_llm.find(target)
    ocr_result = paddle_ocr.find(target)

    log_to_metrics({
        "timestamp": now(),
        "url": current_url,
        "target": target,
        "vlm_bbox": vlm_result,
        "ocr_bbox": ocr_result,
        "match": is_close(vlm_result, ocr_result),
        "used": "ocr" if ocr_result else "vlm"
    })

    return ocr_result or vlm_result
```

### Metrics Dashboard (Future)
```
OCR Accuracy Report - Last 7 Days
---------------------------------
Detection Rate:  87.3%
Avg IoU:         0.82
Fallback Rate:   12.7%

By Site:
  google.com:    94.2%
  amazon.com:    81.5%
  other:         85.1%

By Element Type:
  buttons:       91.2%
  links:         88.4%
  inputs:        72.3%  <- needs improvement
```

## Click Verification Logic

Every click is verified using three layers:

```python
def verify_click(click_func, target_text, target_bbox):
    # Capture before state
    url_before = driver.current_url
    screenshot_before = capture_screenshot()

    # Perform click
    click_func()
    time.sleep(0.3)

    # Layer 1: URL Change (fastest check)
    if driver.current_url != url_before:
        return {
            "success": True,
            "method": "url_change",
            "new_url": driver.current_url
        }

    # Layer 2: Element Disappeared (OCR re-check)
    screenshot_after = capture_screenshot()
    ocr_results = paddle_ocr.find(screenshot_after, target_text)

    if not ocr_results or not bbox_overlaps(ocr_results, target_bbox):
        return {
            "success": True,
            "method": "element_disappeared"
        }

    # Layer 3: Visual Diff (fallback)
    diff_score = compare_screenshots(screenshot_before, screenshot_after)

    if diff_score > VISUAL_DIFF_THRESHOLD:
        return {
            "success": True,
            "method": "visual_diff",
            "diff_score": diff_score
        }

    # All checks failed
    return {
        "success": False,
        "method": "none",
        "screenshots": {
            "before": save_debug_screenshot(screenshot_before),
            "after": save_debug_screenshot(screenshot_after)
        }
    }
```

## Success Criteria Per Milestone

| Milestone | Success Criteria |
|-----------|------------------|
| 1. Foundation | AdsPower API responds, Ollama/Qwen responds |
| 2. Vision Element Finding | VLM finds elements 95%+ on test set, clicks land correctly 90%+ |
| 3. OCR Optimization | OCR matches VLM 80%+ (IoU > 0.7), fallback rate < 20% |
| 4. AI Decision Loop | AI makes reasonable decisions on 5 page types, valid JSON 95%+ |
| 5. Persona System | Same persona = consistent behavior patterns across sessions |
| 6. Session Management | Session survives Ctrl+C, resumes from checkpoint, metrics saved |
| 7. Multi-Site Browsing | Complete 30-min session, visit 5+ sites, 90%+ click success |

## Test Commands

```bash
# Run all tests
pytest tests/ -v

# Run specific test
pytest tests/test_element_accuracy.py -v

# Run with coverage
pytest tests/ --cov=profile_builder --cov-report=html

# Run accuracy comparison (takes longer)
pytest tests/test_element_accuracy.py -v --run-slow
```
