#!/usr/bin/env python3
"""
Context Guard — token checker.
Primary metric: 5-hour plan output budget (tracks what Anthropic's session meter tracks).
Secondary metric: current conversation context window usage.
Usage: python3 check_tokens.py [transcript_path]
"""

import json
import os
import sys
import time
from pathlib import Path
import glob


CONFIG_PATH = Path.home() / ".claude/context-guard/config.json"
FIVE_HOURS = 5 * 3600


def load_config():
    with open(CONFIG_PATH) as f:
        cfg = json.load(f)
    plan_key = cfg.get("active_plan", "pro")
    plan = cfg["plans"].get(plan_key, cfg["plans"]["pro"])
    return cfg, plan_key, plan


def find_latest_transcript(hint_path=None):
    if hint_path and os.path.exists(hint_path):
        return hint_path
    cwd = os.getcwd()
    project_key = cwd.replace("/", "-").lstrip("-")
    for base in [
        Path.home() / ".claude/projects" / project_key,
        Path.home() / ".claude/projects/-Users-traftonobrien-Desktop",
    ]:
        if base.exists():
            files = sorted(base.glob("*.jsonl"), key=lambda f: f.stat().st_mtime, reverse=True)
            if files:
                return str(files[0])
    return None


def parse_transcript(path):
    """Return list of (input, output, cache_read, cache_create, model) per assistant turn."""
    turns = []
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
                        turns.append((
                            u.get("input_tokens", 0),
                            u.get("output_tokens", 0),
                            u.get("cache_read_input_tokens", 0),
                            u.get("cache_creation_input_tokens", 0),
                            model,
                        ))
            except Exception:
                pass
    return turns


def sum_5hr_output_tokens(cfg):
    """Sum output tokens across all transcripts modified in last 5 hours."""
    now = time.time()
    claude_dir = Path.home() / ".claude/projects"
    total_output = 0
    session_count = 0

    for jsonl in claude_dir.rglob("*.jsonl"):
        age = now - jsonl.stat().st_mtime
        if age > FIVE_HOURS:
            continue
        try:
            turns = parse_transcript(str(jsonl))
            out = sum(t[1] for t in turns)
            if out:
                total_output += out
                session_count += 1
        except Exception:
            pass

    return total_output, session_count


def bar(pct, width=38):
    filled = int(width * min(pct, 1.0))
    char = "█" if pct < 0.85 else "▓"
    return char * filled + "░" * (width - filled)


def main():
    hint = sys.argv[1] if len(sys.argv) > 1 else None

    try:
        cfg, plan_key, plan = load_config()
    except Exception as e:
        print(f"Config error: {e}")
        sys.exit(1)

    # ── 5-hr plan budget (PRIMARY) ───────────────────────────────────────────
    budget = plan.get("session_output_budget")
    output_5hr, session_count = sum_5hr_output_tokens(cfg)

    # ── Current conversation context window (SECONDARY) ─────────────────────
    transcript = find_latest_transcript(hint)
    ctx_pct = ctx_total = ctx_window = ctx_turns = 0
    ctx_model = "unknown"
    if transcript and os.path.exists(transcript):
        turns = parse_transcript(transcript)
        if turns:
            last = turns[-1]
            ctx_total = last[0] + last[2] + last[3]
            ctx_turns = len(turns)
            ctx_model = last[4]
            plan_window = plan.get("context_window")
            if plan_window:
                ctx_window = plan_window
            else:
                models = cfg.get("models", {})
                ctx_window = models.get(ctx_model, models.get("_fallback", 200000))
            ctx_pct = ctx_total / ctx_window

    label = plan.get("label", plan_key)
    trigger = plan.get("trigger_threshold", 0.75)

    print(f"\n{'='*52}")
    print(f"  Context Guard — {plan_key.upper()}")
    print(f"  {label}")
    print(f"{'='*52}")

    if budget:
        budget_pct = output_5hr / budget
        trigger_tokens = int(trigger * budget)
        remaining = budget - output_5hr
        status = "🟢 OK" if budget_pct < trigger else "🔴 SAVE NOW — run /session-save"
        print(f"\n  5-HR PLAN BUDGET (primary)")
        print(f"  [{bar(budget_pct)}] {budget_pct*100:.1f}%")
        print(f"  {output_5hr:,} / {budget:,} output tokens used")
        print(f"  Remaining: {remaining:,} output tokens")
        print(f"  Trigger at: {trigger*100:.0f}% ({trigger_tokens:,} tokens)")
        print(f"  Sessions counted: {session_count}")
        print(f"  Status: {status}")
    else:
        print(f"\n  5-hr budget: not configured for API plans (no session window)")

    if ctx_window:
        print(f"\n  CONTEXT WINDOW (current conversation)")
        print(f"  [{bar(ctx_pct)}] {ctx_pct*100:.1f}%")
        print(f"  {ctx_total:,} / {ctx_window:,} tokens")
        print(f"  Model: {ctx_model}  |  Turns: {ctx_turns}")

    print(f"\n{'='*52}\n")


if __name__ == "__main__":
    main()
