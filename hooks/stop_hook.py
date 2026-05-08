#!/usr/bin/env python3
"""
Context Guard — Stop Hook
Fires after every Claude turn. Reads transcript, calculates token usage.
If above threshold, writes flag file so PreToolUse hook can block next tool call.
"""

import json
import os
import sys
from pathlib import Path

CONFIG_PATH = Path.home() / ".claude/context-guard/config.json"


def load_config():
    with open(CONFIG_PATH) as f:
        cfg = json.load(f)
    plan_key = cfg.get("active_plan", "pro")
    plan = cfg["plans"].get(plan_key, cfg["plans"]["pro"])
    return cfg, plan


def get_context_window(cfg, plan: dict, model: str) -> int:
    # Plan-level override takes precedence (e.g. pro_1m sets 1_000_000)
    if "context_window" in plan:
        return plan["context_window"]
    models = cfg.get("models", {})
    return models.get(model, models.get("_fallback", 200000))


def get_latest_usage(transcript_path: str):
    """Return (total_tokens, model) from the last assistant turn."""
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
    if not last:
        return None, None
    u, model = last
    total = (
        u.get("input_tokens", 0)
        + u.get("cache_read_input_tokens", 0)
        + u.get("cache_creation_input_tokens", 0)
    )
    return total, model


def main():
    payload = json.loads(sys.stdin.read())

    if not payload:
        sys.exit(0)

    transcript_path = payload.get("transcript_path")
    session_id = payload.get("session_id", "")

    if not transcript_path or not os.path.exists(transcript_path):
        sys.exit(0)

    try:
        cfg, plan = load_config()
    except Exception as e:
        sys.exit(0)

    if not cfg.get("enabled", True):
        sys.exit(0)

    total_tokens, model = get_latest_usage(transcript_path)
    if total_tokens is None:
        sys.exit(0)

    context_window = get_context_window(cfg, plan, model or "_fallback")
    threshold = plan.get("trigger_threshold", 0.75)
    pct = total_tokens / context_window

    flag_path = cfg.get("flag_path", "/tmp/context-guard-flag.json")

    if pct >= threshold:
        flag = {
            "session_id": session_id,
            "transcript_path": transcript_path,
            "tokens": total_tokens,
            "context_window": context_window,
            "pct": round(pct * 100, 1),
            "threshold_pct": round(threshold * 100, 1),
            "model": model,
            "plan": cfg.get("active_plan"),
        }
        with open(flag_path, "w") as f:
            json.dump(flag, f)
        # Emit summary to stderr (visible in Claude Code debug output)
        print(
            f"[context-guard] ⚠️  {pct*100:.1f}% of context used "
            f"({total_tokens:,}/{context_window:,}). Flag written.",
            file=sys.stderr,
        )
    else:
        # Clear stale flag if session changed or we're well below threshold
        if os.path.exists(flag_path):
            try:
                with open(flag_path) as f:
                    existing = json.load(f)
                if existing.get("session_id") != session_id:
                    os.remove(flag_path)
            except Exception:
                pass
        print(
            f"[context-guard] {pct*100:.1f}% ({total_tokens:,}/{context_window:,} tokens)",
            file=sys.stderr,
        )

    sys.exit(0)


if __name__ == "__main__":
    main()
