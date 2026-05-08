---
name: tokens
description: |
  Check current Claude Code session token usage. Shows context %, tokens used/remaining,
  threshold, and model. Part of context-guard: github.com/traftonobrien/context-guard
trigger: /tokens
---

# Token Usage Check

Run this command and report the output to the user:

```bash
python3 ~/.claude/context-guard/check_tokens.py
```

Report the output exactly as-is. No additional commentary unless the status is
🔴 OVER THRESHOLD, in which case also tell the user to run `/session-save` immediately.
