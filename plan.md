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

### Milestone 3: AI Decision Loop (IN PROGRESS)
**Goal: Human-like browsing** - AI browses fashion sites with realistic behavior
**Test Profile**: k18il1i6

**Human-Like Requirements**:
- Dwell time: 5-30s after clicks (simulates reading/viewing)
- Click variety: Mix of items, images, categories (not just scrolling)
- Search behavior: Start with search, explore results naturally
- Natural flow: Search → Browse → Click item → View → Back → Explore

**Already Drafted** (untracked, ready to commit):
- [x] Structured action schema (ai/actions.py) - CLICK, TYPE, SCROLL, WAIT, NAVIGATE
- [x] Decision maker (ai/decision_maker.py) - VLM decides actions with safety checks
- [x] Session planner (ai/session_planner.py) - NEWS, YOUTUBE, FASHION, FORUMS, SHOPPING
- [x] Safety checker (core/safety.py) - Blocks logout, purchases, form submissions

**To Build**:
- [ ] Action executor (ai/action_executor.py) - Execute actions using input modules
- [ ] Browsing session (core/session.py) - Main loop with human-like timing
- [ ] CLI entry point (run.py) - `python run.py browse <profile_id> --structure fashion`
- [ ] Tests (tests/test_milestone3.py)

**Timing Constants**:
- DWELL_TIME: 5-30s after clicking items
- SCROLL_PAUSE: 2-5s after scrolling
- ACTION_COOLDOWN: 1-2s between actions

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
