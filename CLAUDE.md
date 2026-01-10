# Profile Builder

Browser profile warming system for e-commerce. Builds cookies/reputation over sessions.

## Core Loop
Screenshot (720p) -> AI decides -> Find element -> Human click -> Verify -> Repeat

## Stack
- AdsPower (fingerprints)
- Qwen2.5-VL-7B via Ollama (decisions)
- PaddleOCR (fast element finding)
- HumanCursor (mouse)
- OS-level input only (never Selenium click/keys)

## Architecture
- Top-down element finding: VLM baseline -> OCR optimization
- Persona system: each profile has consistent browsing personality
- Dual-purpose verification: runtime fallback + testing

## Current Status
See `plan.md` for milestones and progress.

## Docs
- `docs/architecture.md` - System design and diagrams
- `docs/technical-decisions.md` - Why we made each choice
- `docs/persona-system.md` - Persona schema and usage
- `docs/testing-strategy.md` - How we validate accuracy
- `docs/external-integrations.md` - HumanCursor, PaddleOCR, AdsPower, Ollama
- `docs/workflow-rules.md` - Focus guards and development rules
- `docs/known-issues.md` - Problems and mitigations
- `docs/quickstart.md` - Setup and first run

## Rules
1. Max 2 attempts on same error, then ask
2. Save progress to plan.md before milestone ends
3. Git branch before changes
4. If context heavy, tell user to /clear
5. Strict milestones - complete before moving on
6. OS-level input ONLY - never use Selenium .click() or .send_keys()
7. Tests MUST pass + human approval before milestone complete
