#!/usr/bin/env python3
"""
Context Guard — PreToolUse Hook
If a context-limit flag exists for the current session, blocks ALL tool calls
and instructs Claude to run /session-save before continuing.
"""

import json
import os
import sys
from pathlib import Path

CONFIG_PATH = Path.home() / ".claude/context-guard/config.json"


def main():
    payload = json.loads(sys.stdin.read())
    session_id = payload.get("session_id", "")
    tool_name = payload.get("tool_name", "")

    try:
        with open(CONFIG_PATH) as f:
            cfg = json.load(f)
        if not cfg.get("enabled", True):
            sys.exit(0)
        flag_path = cfg.get("flag_path", "/tmp/context-guard-flag.json")
    except Exception:
        sys.exit(0)

    if not os.path.exists(flag_path):
        sys.exit(0)

    try:
        with open(flag_path) as f:
            flag = json.load(f)
    except Exception:
        sys.exit(0)

    # Only block if flag is for THIS session
    if flag.get("session_id") != session_id:
        sys.exit(0)

    pct = flag.get("pct", "?")
    threshold = flag.get("threshold_pct", "?")
    tokens = flag.get("tokens", 0)
    window = flag.get("context_window", 200000)
    model = flag.get("model", "unknown")

    # Output block decision — Claude Code reads this from stdout
    block_msg = (
        f"🛑 Context Guard: {pct}% of context window used "
        f"({tokens:,}/{window:,} tokens, model: {model}). "
        f"Threshold: {threshold}%. "
        f"Run /session-save NOW to generate summary, next-steps, and resume docs "
        f"before context is lost. Tool call '{tool_name}' blocked."
    )

    print(json.dumps({"decision": "block", "reason": block_msg}))
    sys.exit(0)


if __name__ == "__main__":
    main()
