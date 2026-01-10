# Workflow Rules

These rules prevent Claude Code from losing context and spiraling into self-diagnosis loops.

## 1. Save Progress Before Milestone Ends

Before marking a milestone complete:
```bash
# Update plan.md with progress
- Mark completed tasks with [x]
- Note any issues discovered
- Document any deviations from plan
```

This ensures the next session knows exactly where we left off.

## 2. Run /clear Between Milestones

After completing a milestone:
1. User runs `/clear` command
2. Fresh context for next milestone
3. Claude re-reads CLAUDE.md and plan.md
4. Continue from documented state

This prevents context bloat from accumulating.

## 3. Git Branch Before Changes

Before starting any code changes:
```bash
git checkout -b milestone-X-description
```

Examples:
- `milestone-1-foundation`
- `milestone-2-vision-element-finding`
- `milestone-3-ocr-optimization`

This allows easy rollback if something goes wrong.

## 4. Max 2 Attempts on Same Error

If an error occurs:
1. First attempt: Try to fix based on error message
2. Second attempt: Try alternative approach

If still failing after 2 attempts:
- STOP
- Ask user for guidance
- Do NOT spiral into auto-diagnosis

```python
# Bad (spiral)
for i in range(10):
    try_different_thing()  # Just guessing

# Good (bounded)
try:
    approach_1()
except:
    try:
        approach_2()
    except:
        ask_user("Failed twice, need guidance")
```

## 5. Tell User When Context Gets Heavy

Signs of heavy context:
- Conversation is very long
- Multiple large file reads
- Many error traces accumulated
- Responses getting slower

When this happens:
```
"Context is getting heavy. I recommend:
1. I'll save progress to plan.md
2. You run /clear
3. We continue fresh"
```

## 6. Strict Milestones - No Skipping

Each milestone must be COMPLETE before moving to next:
- All tasks checked off
- Success criteria met
- Tests passing (if applicable)
- Progress saved to plan.md

No "I'll come back to this later" - finish what's started.

## 7. Ask, Don't Assume

When uncertain about:
- User's intent
- Which approach to take
- Whether behavior is expected

ASK the user. Don't make assumptions and build on them.

## Summary Checklist

Before ending any work session:
- [ ] Progress saved to plan.md
- [ ] Current milestone status clear
- [ ] Any blockers documented
- [ ] Git committed (if code changed)

Before starting new milestone:
- [ ] Previous milestone complete
- [ ] /clear run (fresh context)
- [ ] New git branch created
- [ ] plan.md reviewed for current state
