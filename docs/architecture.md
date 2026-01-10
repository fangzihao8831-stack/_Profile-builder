# Architecture

## Session Loop

```
+---------------------------------------------------------------------+
|                         SESSION LOOP                                |
+---------------------------------------------------------------------+
|                                                                     |
|  1. CAPTURE                                                         |
|     |  Screenshot current browser state                             |
|     |  Resize to 720p for VLM                                       |
|     v                                                               |
|  2. DECIDE (Qwen2.5-VL-7B)                                          |
|     |  Input: screenshot + persona + context                        |
|     |  Output: structured JSON action                               |
|     v                                                               |
|  3. LOCATE (Element Finding Cascade)                                |
|     |  VLM baseline -> OCR optimization -> CSS patterns             |
|     |  Returns: bounding box coordinates                            |
|     v                                                               |
|  4. EXECUTE (OS-Level Input)                                        |
|     |  HumanCursor for mouse (bezier curves)                        |
|     |  PyAutoGUI for keyboard                                       |
|     |  Never Selenium .click() or .send_keys()                      |
|     v                                                               |
|  5. VERIFY                                                          |
|     |  Check: URL changed? Element gone? Visual diff?               |
|     |  If failed: retry or ask AI for alternative                   |
|     v                                                               |
|  REPEAT until session time expires                                  |
|                                                                     |
+---------------------------------------------------------------------+
```

## Element Finding Cascade (Top-Down)

We build top-down for reliability:

```
+---------------------------------------------------------------------+
|                    ELEMENT FINDING CASCADE                          |
+---------------------------------------------------------------------+
|                                                                     |
|  AI decides: "click Add to Cart"                                    |
|                    |                                                |
|                    v                                                |
|  +---------------------------------------------------------------+  |
|  | LAYER 1: PaddleOCR (50-100ms)                                 |  |
|  | - Find text "Add to Cart" in screenshot                       |  |
|  | - Returns bounding box if found                               |  |
|  | - FASTEST but text-only                                       |  |
|  +---------------------------------------------------------------+  |
|                    |                                                |
|           Found? --+-- Not found                                    |
|             |              |                                        |
|             v              v                                        |
|          USE IT    +---------------------------------------------+  |
|                    | LAYER 2: CSS Selectors (<10ms)              |  |
|                    | - Known patterns for major sites            |  |
|                    | - e.g., Amazon: #add-to-cart-button         |  |
|                    | - SITE-SPECIFIC database                    |  |
|                    +---------------------------------------------+  |
|                              |                                      |
|                     Found? --+-- Not found                          |
|                       |              |                              |
|                       v              v                              |
|                    USE IT    +-------------------------------------+|
|                              | LAYER 3: Vision LLM (500-2000ms)    ||
|                              | - Ask Qwen: "Where is X?"           ||
|                              | - Can find icons, images, shapes    ||
|                              | - ALWAYS WORKS (baseline)           ||
|                              +-------------------------------------+|
|                                                                     |
+---------------------------------------------------------------------+
```

**Why top-down?**
- VLM is built and tested FIRST as reliable baseline
- OCR is added as OPTIMIZATION, tested against VLM accuracy
- If fast layers fail, VLM fallback is always available
- Bottom-up risk: if top layers fail, no safety net

## Component Relationships

```
+---------------------------------------------------------------------+
|                      COMPONENT DIAGRAM                              |
+---------------------------------------------------------------------+
|                                                                     |
|  +--------------+         +----------------------------------+      |
|  |   AdsPower   |<------->|         browser/adspower.py      |      |
|  |   (External) |         |  - Start/stop profiles           |      |
|  +--------------+         |  - Get browser connection        |      |
|                           +----------------------------------+      |
|                                        |                            |
|                                        v                            |
|  +--------------+         +----------------------------------+      |
|  |    Ollama    |<------->|         ai/ollama_client.py      |      |
|  |   (External) |         |  - Qwen2.5-VL-7B interface       |      |
|  |              |         |  - keep_alive for VRAM           |      |
|  +--------------+         |  - Structured JSON output        |      |
|                           +----------------------------------+      |
|                                        |                            |
|                                        v                            |
|                           +----------------------------------+      |
|                           |        ai/decision.py            |      |
|                           |  - Parse AI response to action   |      |
|                           |  - Validate action schema        |      |
|                           +----------------------------------+      |
|                                        |                            |
|                                        v                            |
|                           +----------------------------------+      |
|                           |       element/finder.py          |      |
|                           |  - Unified element finding       |      |
|                           |  - Cascade: OCR -> CSS -> VLM    |      |
|                           |  - Dual-mode logging             |      |
|                           +----------------------------------+      |
|                                        |                            |
|                                        v                            |
|                           +----------------------------------+      |
|                           |      input/coordinates.py        |      |
|                           |  - Image space -> screen space   |      |
|                           |  - DPI awareness                 |      |
|                           |  - 720p reverse mapping          |      |
|                           +----------------------------------+      |
|                                        |                            |
|                                        v                            |
|  +--------------+         +----------------------------------+      |
|  | HumanCursor  |<------->|        input/mouse.py            |      |
|  |  (Library)   |         |  - Bezier curve movement         |      |
|  +--------------+         |  - OS-level clicks               |      |
|                           +----------------------------------+      |
|                                        |                            |
|                                        v                            |
|                           +----------------------------------+      |
|                           |  verification/click_verifier.py  |      |
|                           |  - URL change detection          |      |
|                           |  - Element disappearance (OCR)   |      |
|                           |  - Visual diff fallback          |      |
|                           +----------------------------------+      |
|                                                                     |
+---------------------------------------------------------------------+
```

## Structured JSON Output Format

### AI Decision Response
```json
{
  "action": "click",
  "target": "Add to Cart",
  "reasoning": "Product page loaded, adding item to cart"
}
```

```json
{
  "action": "search_google",
  "query": "nike air max 90 mens",
  "reasoning": "Starting search for target product category"
}
```

```json
{
  "action": "scroll",
  "direction": "down",
  "amount": "half_page",
  "reasoning": "Need to see more products"
}
```

```json
{
  "action": "type",
  "target": "search box",
  "text": "running shoes",
  "reasoning": "Searching within site"
}
```

### Coordinate Response (Element Finding)
```json
{
  "found": true,
  "target": "Add to Cart",
  "bbox": {
    "x1": 850,
    "y1": 420,
    "x2": 980,
    "y2": 460
  },
  "center": {
    "x": 915,
    "y": 440
  },
  "confidence": 0.95
}
```

### Action Types
| Action | Required Fields | Optional Fields |
|--------|-----------------|-----------------|
| click | target | - |
| scroll | direction | amount |
| type | target, text | - |
| search_google | query | - |
| wait | duration | reason |
| navigate | url | - |
