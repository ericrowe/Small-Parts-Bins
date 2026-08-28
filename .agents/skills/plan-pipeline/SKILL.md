---
name: plan-pipeline
description: >-
  Manage the structured milestone and task pipeline under Plans/. Use this skill
  when creating a new numbered plan, transitioning plan states, checking pipeline
  integrity, or archiving a completed plan with its walkthrough narrative.
---

# Plan Pipeline Management Skill

This skill enforces high-discipline task execution, dependency tracking, and documentation archiving across the lifecycle of every project milestone.

## Plan Pipeline Directory Structure

```text
Plans/
├── PRIORITIES.md        # Ranked queue of active and planned work
├── check_pipeline.py    # Pipeline validator script
├── 001-my-first-plan.md # Active/In-work plan file
├── Queued/              # Drafted future plans waiting for dependency resolution
└── Completed/           # Historical archive of completed plans and walkthroughs
```

## How to Work the Pipeline

### 1. Starting a New Plan
1. Draft a new numbered plan (e.g. `Plans/001-architecture-baseline.md`).
2. Include: Status, Depends on, Outcome, Requirements, Non-goals, Implementation steps (checkboxes), and Acceptance criteria.
3. Update `Plans/PRIORITIES.md` to list the plan in the active queue.
4. Verify with:
   ```bash
   python3 Plans/check_pipeline.py
   ```

### 2. Executing Work
- Update implementation checkboxes as each technical step is verified.
- Commit code and test artifacts incrementally.
- Push commits offsite (`git push origin main`).

### 3. Completing and Archiving a Plan
1. Move/copy the plan to `Plans/Completed/YYYY-MM-DD-NNN-<name>.md`.
2. Create a matching narrative walkthrough: `Plans/Completed/YYYY-MM-DD-NNN-<name>-walkthrough.md`.
3. Update `Plans/PRIORITIES.md` to remove the completed plan and promote the next queued plan.
4. Update `README.md` and `AGENTS.md` to record the verified baseline.
5. Run `python3 Plans/check_pipeline.py` to confirm 0 pipeline violations.
6. Commit and push.
