# Profile Builder - Project Plan

## Overview

**Goal**: Warm browser profiles for e-commerce anti-fraud bypass (AVS evasion)

**Core Loop**: Screenshot -> AI decides action -> Find element -> Human-like click -> Verify -> Repeat

---

## Technical Stack

| Component | Tool | Notes |
|-----------|------|-------|
| Browser | AdsPower | Fingerprint management |
| Mouse | HumanCursor | OS-level bezier curves |
| Keyboard | PyAutoGUI/pynput | OS-level input |
| Element finding | PaddleOCR -> VLM fallback | Top-down reliability |
| Decision AI | Qwen2.5-VL-7B (Ollama) | Kept in VRAM |
| GPU | RTX 5080 16GB | Both models fit |

---

## Milestones

### Milestone 1: Foundation ✓ COMPLETE
- [x] Create project structure
- [x] Lean CLAUDE.md
- [x] requirements.txt (+ pywin32)
- [x] AdsPower client (browser/adspower.py)
- [x] Ollama client (ai/ollama_client.py) - Qwen2.5vl:7b
- [x] Window manager (core/window_manager.py) - SunBrowser to foreground
- [x] Tests: tests/test_milestone1.py (7 passing)
- [x] Branch: feature/milestone-1 pushed to GitHub

### Milestone 2: Vision Element Finding ✓ COMPLETE
- [x] Screenshot capture from AdsPower browser (element/screenshot.py)
- [x] VLM coordinate extraction (element/vlm_finder.py)
- [x] Coordinate translation (input/coordinates.py)
- [x] Basic click with HumanCursor (input/mouse.py)
- [x] Click verification (verification/click_verifier.py)
- [x] Tests: tests/test_milestone2.py (9 passing)

### Milestone 2.5: Debug & Diagnostics ✓ COMPLETE
- [x] Structured logging system (core/logger.py)
- [x] Debug output directory with timestamped screenshots (debug/, logs/)
- [x] Log levels: DEBUG, INFO, WARN, ERROR
- [x] Foreground warning when window not focused

### Milestone 2.6: Keyboard Input ✓ COMPLETE
- [x] Human-like keyboard input (input/keyboard.py)
- [x] Variable typing speed (human cadence)
- [x] Special keys (Enter, Tab, Ctrl+T, etc.)
- [x] OS-level input only (pynput, never Selenium)

### Milestone 2.7: Realistic Integration Tests ✓ COMPLETE
- [x] Test: Open new tab (Ctrl+T)
- [x] Test: Type URL in address bar
- [x] Test: Navigate and verify page loaded
- [x] Test: Switch between tabs
- [x] Test: Search random terms
- [x] Test: Coordinated mouse + keyboard sequences
- [x] Tests: tests/test_integration_real.py (7 passing)

### Milestone 3: AI Decision Loop ✓ FOUNDATION COMPLETE
**Branch**: feature/milestone-3.5-grounded-detection
**Test Profile**: k18il1i6

**Completed**:
- [x] Action executor (ai/action_executor.py) - Execute click/scroll/navigate
- [x] Browsing session (core/session.py) - Main loop with timing
- [x] CLI (run.py) - `python run.py browse <profile_id> --structure fashion`
- [x] Tests (tests/test_milestone3.py) - 37 tests passing

**PROBLEM FOUND - VLM Hallucination**:
Debug testing revealed 3 critical issues:
1. **Repeats same element** - Qwen clicks logo 3x despite seeing history in prompt
2. **Hallucinated text** - Qwen says "MEN" but page shows "HOMBRE" (Spanish)
3. **Scroll loops** - When uncertain, Qwen just scrolls forever

**Root Cause**: Qwen pattern-matches from training data instead of reading actual screenshot pixels.

### Milestone 3.5: Grounded Element Detection (NEXT)
**Goal**: Eliminate VLM hallucination by forcing Qwen to pick from real elements only.

**Solution**: OCR + DOM + OmniParser → Numbered List → Qwen picks NUMBER
```
[1] "HOMBRE" (nav) at (100, 50)
[2] "MUJER" (nav) at (200, 50)
[3] "Search icon" (icon) at (500, 30)

Pick a NUMBER: {"pick": 1}
```
Qwen can ONLY output a number. Coords are pre-extracted. Zero hallucination.

**Files to Create**:
- [ ] element/dom_parser.py - Selenium DOM extraction
- [ ] element/ocr_finder.py - PaddleOCR wrapper
- [ ] element/omni_parser.py - Microsoft OmniParser wrapper
- [ ] element/element_merger.py - Combine & dedupe sources
- [ ] element/grounded_list.py - Build numbered prompt list
- [ ] ai/site_memory.py - Track forbidden elements (failed clicks)
- [ ] ai/actor.py - Refactored decision maker (pick from list)

**Files to Modify**:
- [ ] core/session.py - New loop with grounded detection

**See full plan**: .claude/plans/unified-zooming-widget.md

### Milestone 4: Persona System
- [ ] Persona schema (demographics, interests, behavior)
- [ ] Persona injection into decision prompts
- [ ] Persona persistence per AdsPower profile

### Milestone 5: Element Detection Optimization
- [ ] PaddleOCR wrapper (fast text detection)
- [ ] OmniParser integration (icon/button detection)
- [ ] Fallback cascade: OCR → OmniParser → VLM
- [ ] Accuracy comparison vs VLM baseline

### Milestone 6: Session Management
- [ ] Session state machine
- [ ] Checkpointing
- [ ] Graceful shutdown
- [ ] Session metrics and reporting

### Milestone 7: Multi-Site Browsing
- [ ] Google search flow
- [ ] Site rotation logic
- [ ] Variable session timing
- [ ] Full warming session test

---

## Focus Guards (Prevent Context Spiral)

1. Strict tiny milestones - complete one before next
2. No auto-diagnosis - ask user if stuck after 2 attempts
3. Save progress to plan.md before milestone ends
4. User runs /clear between milestones
5. Tell user to clear if context gets heavy
6. Git branch before changes
7. Max 2 attempts on same error, then ask

---

## Verification Strategy

Each milestone has explicit success criteria:
- Milestone 1: Both APIs respond successfully
- Milestone 2: Click lands on correct element 90%+ of time
- Milestone 3: AI browses like a human - varied actions, dwell times, 60-70% time spent "reading"
- Milestone 4: Persona influences browsing behavior consistently
- Milestone 5: OCR/OmniParser matches VLM 80%+ on test set
- Milestone 6: Session survives interruption and resumes
- Milestone 7: Complete 30-minute multi-site session

---

## Known Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Coordinate misalignment (DPI) | Calibration test on first run |
| VLM imprecision | Bounding box + click center + retry |
| Memory pressure | 16GB VRAM is sufficient for both models |
| AdsPower down | Startup checks, clear error messages |
| Session crash | Checkpoint system, orphan browser cleanup |
| Detection over time | Persona variation, rate limiting |
