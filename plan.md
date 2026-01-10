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

### Milestone 1: Foundation
- [ ] Create project structure
- [ ] Lean CLAUDE.md
- [ ] requirements.txt
- [ ] AdsPower connection test
- [ ] Ollama connection test (Qwen2.5-VL)

### Milestone 2: Vision Element Finding
- [ ] Screenshot capture from AdsPower browser
- [ ] VLM coordinate extraction (bounding box JSON)
- [ ] Coordinate translation (image space -> screen space)
- [ ] Basic click with HumanCursor
- [ ] Click verification (URL change / visual diff)

### Milestone 3: OCR Optimization
- [ ] PaddleOCR wrapper
- [ ] Accuracy comparison vs VLM baseline
- [ ] Fallback cascade (OCR -> VLM)
- [ ] Dual-mode logging (production + testing)

### Milestone 4: AI Decision Loop
- [ ] Structured action schema
- [ ] Decision prompt with context (URL, history, goal)
- [ ] Action executor (click, scroll, type, navigate)
- [ ] Page load detection

### Milestone 5: Persona System
- [ ] Persona schema (demographics, behavior, habits)
- [ ] Persona injection into prompts
- [ ] Persona persistence per AdsPower profile

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
- Milestone 3: OCR matches VLM 80%+ on test set
- Milestone 4: AI makes reasonable decisions on 5 different page types
- Milestone 5: Persona influences behavior consistently
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
