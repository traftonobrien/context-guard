#!/usr/bin/env python3
"""
Context Guard — Stop Hook
Fires after every Claude turn.
Primary trigger: 5-hour plan output budget (matches Anthropic's session meter).
Secondary check: context window (fires at ~84% auto-compact wall regardless).
"""

import json
import os
import sys
import time
from pathlib import Path

CONFIG_PATH = Path.home() / ".claude/context-guard/config.json"
FIVE_HOURS = 5 * 3600


def load_config():
    with open(CONFIG_PATH) as f:
        cfg = json.load(f)
    plan_key = cfg.get("active_plan", "pro")
    plan = cfg["plans"].get(plan_key, cfg["plans"]["pro"])
    return cfg, plan_key, plan


def get_context_window(cfg, plan, model):
    if "context_window" in plan:
        return plan["context_window"]
    models = cfg.get("models", {})
    return models.get(model, models.get("_fallback", 200000))


def parse_last_turn(transcript_path):
    """Return usage dict and model from most recent assistant turn."""
    last = None
    with open(transcript_path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                if obj.get("type") == "assistant" and "message" in obj:
                    u = obj["message"].get("usage")
                    model = obj["message"].get("model", "_fallback")
                    if u:
                        last = (u, model)
            except Exception:
                pass
    return last


def sum_5hr_output_tokens():
    """Sum output tokens across all transcripts modified in last 5 hours."""
    now = time.time()
    claude_dir = Path.home() / ".claude/projects"
    total = 0
    for jsonl in claude_dir.rglob("*.jsonl"):
        age = now - jsonl.stat().st_mtime
        if age > FIVE_HOURS:
            continue
        try:
            with open(jsonl) as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        obj = json.loads(line)
                        if obj.get("type") == "assistant" and "message" in obj:
                            u = obj["message"].get("usage", {})
                            if u:
                                total += u.get("output_tokens", 0)
                    except Exception:
                        pass
        except Exception:
            pass
    return total


def main():
    payload = json.loads(sys.stdin.read())
    if not payload:
        sys.exit(0)

    transcript_path = payload.get("transcript_path")
    session_id = payload.get("session_id", "")

    if not transcript_path or not os.path.exists(transcript_path):
        sys.exit(0)

    try:
        cfg, plan_key, plan = load_config()
    except Exception:
        sys.exit(0)

    if not cfg.get("enabled", True):
        sys.exit(0)

    threshold = plan.get("trigger_threshold", 0.75)
    flag_path = cfg.get("flag_path", "/tmp/context-guard-flag.json")

    # ── Primary: 5-hr plan budget ────────────────────────────────────────────
    budget = plan.get("session_output_budget")
    triggered = False
    trigger_reason = None
    output_5hr = 0

    if budget:
        output_5hr = sum_5hr_output_tokens()
        budget_pct = output_5hr / budget
        if budget_pct >= threshold:
            triggered = True
            trigger_reason = f"5-hr plan budget at {budget_pct*100:.1f}% ({output_5hr:,}/{budget:,} output tokens)"

    # ── Secondary: context window (catch-all near auto-compact wall) ─────────
    ctx_total = ctx_pct = 0
    model = "_fallback"
    last = parse_last_turn(transcript_path)
    if last:
        u, model = last
        ctx_total = (
            u.get("input_tokens", 0)
            + u.get("cache_read_input_tokens", 0)
            + u.get("cache_creation_input_tokens", 0)
        )
        ctx_window = get_context_window(cfg, plan, model)
        ctx_pct = ctx_total / ctx_window
        # Always block at 80% context window regardless of plan budget
        if ctx_pct >= 0.80 and not triggered:
            triggered = True
            trigger_reason = f"context window at {ctx_pct*100:.1f}% ({ctx_total:,}/{ctx_window:,} tokens)"

    if triggered:
        flag = {
            "session_id": session_id,
            "transcript_path": transcript_path,
            "trigger_reason": trigger_reason,
            "output_5hr": output_5hr,
            "budget": budget,
            "budget_pct": round(output_5hr / budget * 100, 1) if budget else None,
            "ctx_tokens": ctx_total,
            "ctx_pct": round(ctx_pct * 100, 1),
            "model": model,
            "plan": plan_key,
            "threshold_pct": round(threshold * 100, 1),
        }
        with open(flag_path, "w") as f:
            json.dump(flag, f)
        print(f"[context-guard] 🚨 TRIGGERED: {trigger_reason}", file=sys.stderr)
    else:
        # Clear stale flag from a different session
        if os.path.exists(flag_path):
            try:
                with open(flag_path) as f:
                    existing = json.load(f)
                if existing.get("session_id") != session_id:
                    os.remove(flag_path)
            except Exception:
                pass
        budget_str = f"  |  5hr plan: {output_5hr/budget*100:.1f}%" if budget else ""
        print(
            f"[context-guard] ctx={ctx_pct*100:.1f}%{budget_str}",
            file=sys.stderr,
        )

    sys.exit(0)


if __name__ == "__main__":
    main()
