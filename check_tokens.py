#!/usr/bin/env python3
"""Quick token check for current Claude Code session. Usage: python3 check_tokens.py [transcript_path]"""

import json
import os
import sys
from pathlib import Path
import glob


def find_latest_transcript():
    """Find most recently modified transcript for current project."""
    # Map cwd to Claude project dir
    cwd = os.getcwd()
    project_key = cwd.replace("/", "-").lstrip("-")
    project_dir = Path.home() / ".claude/projects" / project_key
    if not project_dir.exists():
        # Try Desktop fallback
        project_dir = Path.home() / ".claude/projects/-Users-traftonobrien-Desktop"
    if not project_dir.exists():
        return None
    files = sorted(project_dir.glob("*.jsonl"), key=lambda f: f.stat().st_mtime, reverse=True)
    return str(files[0]) if files else None


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else find_latest_transcript()
    if not path or not os.path.exists(path):
        print("No transcript found")
        sys.exit(1)

    cfg_path = Path.home() / ".claude/context-guard/config.json"
    with open(cfg_path) as f:
        cfg = json.load(f)
    plan_key = cfg.get("active_plan", "pro")
    threshold = cfg["plans"][plan_key]["trigger_threshold"]

    assistants = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                if obj.get("type") == "assistant" and "message" in obj:
                    u = obj["message"].get("usage", {})
                    model = obj["message"].get("model", "_fallback")
                    if u:
                        total = (
                            u.get("input_tokens", 0)
                            + u.get("cache_read_input_tokens", 0)
                            + u.get("cache_creation_input_tokens", 0)
                        )
                        assistants.append((total, model))
            except Exception:
                pass

    if not assistants:
        print("No assistant turns found")
        sys.exit(1)

    total, model = assistants[-1]
    models = cfg.get("models", {})
    window = models.get(model, models.get("_fallback", 200000))
    pct = total / window * 100
    trigger_tokens = int(threshold * window)
    remaining = window - total

    bar_len = 40
    filled = int(bar_len * total / window)
    bar = "█" * filled + "░" * (bar_len - filled)

    status = "🟢 OK" if pct < threshold * 100 else "🔴 OVER THRESHOLD — run /session-save"

    print(f"\n{'='*50}")
    print(f"  Context Guard — {plan_key.upper()} plan")
    print(f"{'='*50}")
    print(f"  [{bar}] {pct:.1f}%")
    print(f"  {total:,} / {window:,} tokens")
    print(f"  Remaining: {remaining:,} tokens")
    print(f"  Threshold: {threshold*100:.0f}% ({trigger_tokens:,} tokens)")
    print(f"  Model: {model}")
    print(f"  Turns: {len(assistants)}")
    print(f"  Status: {status}")
    print(f"{'='*50}\n")


if __name__ == "__main__":
    main()
