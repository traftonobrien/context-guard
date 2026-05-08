---
name: session-save
description: |
  Context Guard session save. Triggered manually (/session-save) or auto-blocked by
  context-guard hook at configured threshold. Generates 3 high-quality handoff docs
  (session summary, next steps, resume doc) using full live context, then clears
  the guard flag. Part of context-guard: github.com/traftonobrien/context-guard
trigger: /session-save
---

# Context Guard — Session Save

Context window is near its limit (or you invoked this manually). Generate 3 handoff documents now, while full context is live. These docs must be good enough that a fresh AI or human can resume without asking any clarifying questions.

---

## Step 1 — Collect Hard Facts

Run these commands. Record every output — you will need it to fill the docs.

```bash
# Location and git state
pwd
git log --oneline -10 2>/dev/null || echo "no git"
git diff --stat HEAD 2>/dev/null || echo "no staged diff"
git status --short 2>/dev/null || echo "no status"
git show --stat HEAD --format="%H %s" 2>/dev/null | head -3
```

Also collect from memory (no tool call needed):
- Every task completed this session
- Every file you edited and why
- Every decision made (especially non-obvious ones)
- Every approach that failed and why
- Exact current task and where it was left
- Whether the codebase is in a broken/half-done state

---

## Step 2 — Create Output Directory

```bash
SESSION_DIR="$(pwd)/.claude/sessions/$(date +%Y-%m-%d-%H%M%S)"
mkdir -p "$SESSION_DIR"
echo "$SESSION_DIR"
```

If `$(pwd)` has no `.claude/` dir, use `~/.claude/sessions/$(date +%Y-%m-%d-%H%M%S)/` instead.

---

## Step 3 — Write `session_summary.md`

Use template at `~/.claude/context-guard/templates/session_summary.md`.

**Quality bar:**
- Accomplishments: specific enough that you could file a PR description from this list
- Decisions: the WHY, not the WHAT — what would a new dev need to know to maintain this code
- Dead ends: if you tried an approach and abandoned it, name it explicitly so the next session doesn't repeat it
- Codebase state: is anything broken? Any half-implemented features? Tests failing?

---

## Step 4 — Write `next_steps.md`

Use template at `~/.claude/context-guard/templates/next_steps.md`.

**Quality bar:**
- IMMEDIATE FIRST ACTION: one sentence, no ambiguity, executable without context
- Task queue: each item must be specific enough that a new Claude session could execute it without reading the summary first
- Re-establish commands: `git log`, `npm run dev`, whatever gets the environment live fastest
- Do NOT Do: if there were any approaches you explicitly decided against, list them here — this prevents the next session from going down dead ends

---

## Step 5 — Write `resume_doc.md`

Use template at `~/.claude/context-guard/templates/resume_doc.md`.

This is the most important document. A fresh AI (Codex, new Claude, GPT-4) with zero context must be able to read this and start working immediately. Write it assuming the reader has never seen this codebase before.

**Quality bar:**
- Project one-liner: what does this actually DO in one sentence
- Architecture notes: the 3-5 things that will cause bugs if the reader doesn't know them (implicit invariants, non-obvious data flows, "never do X because Y")
- Read these files first: not a directory listing — the specific files that give the highest signal about how this codebase works
- In-progress work: what's genuinely half-done and what the completion criteria is
- Do NOT do table: every dead end tried this session
- Key patterns: conventions that exist for a reason (not style preferences — things that will silently break if violated)
- Verification: concrete commands to confirm it's working after changes

---

## Step 6 — Update `~/.claude/primer.md`

Rewrite primer.md completely with the new state. Format must match what's already there. Under 100 lines. Include exact next action.

---

## Step 7 — Clear Guard Flag

```bash
rm -f /tmp/context-guard-flag.json && echo "✓ guard flag cleared"
```

---

## Step 8 — Report

Tell the user:
1. Path to the 3 docs (exact paths)
2. Current token usage (run `python3 ~/.claude/context-guard/check_tokens.py`)
3. That they should run `/compact` now

**Do NOT run `/compact` yourself. The user must trigger it.**

---

## Failure Mode

If you cannot complete all 3 docs before hitting the actual context limit:
1. Prioritize `resume_doc.md` — it carries the most critical info
2. Then `next_steps.md`
3. `session_summary.md` last (most recoverable from git history)
