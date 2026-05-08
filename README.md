# context-guard

Automatic context window monitor for [Claude Code](https://claude.ai/code). Watches token usage every turn, warns you at a configurable threshold, and helps generate high-quality handoff documents before your context is lost.

## What It Does

1. **Monitors** — after every Claude turn, reads your session transcript and calculates exact token usage (`input + cache_read + cache_creation`)
2. **Warns** — when usage crosses your threshold (default 75%), sets a flag
3. **Blocks** — on the next tool call, blocks execution and tells Claude to run `/session-save`
4. **Saves** — `/session-save` generates 3 handoff docs using full live context, then you run `/compact`

### The 3 Documents

| Doc | Purpose |
|-----|---------|
| `session_summary.md` | What happened — accomplishments, decisions, bugs fixed, dead ends |
| `next_steps.md` | Where to go — immediate first action, task queue, blockers |
| `resume_doc.md` | AI-to-AI handoff — full context for Codex, a new Claude session, or any LLM with zero prior context |

## Install

```bash
git clone https://github.com/YOUR_USERNAME/context-guard.git
cd context-guard
chmod +x install.sh
./install.sh
```

The installer:
- Copies files to `~/.claude/context-guard/`
- Copies `/session-save` and `/tokens` skills to `~/.claude/skills/`
- Patches `~/.claude/settings.json` to wire the hooks

## Usage

After install, everything runs automatically. Two commands available in Claude Code:

**Check token usage anytime:**
```
/tokens
```

**Manually trigger a session save:**
```
/session-save
```

## Configuration

Edit `~/.claude/context-guard/config.json`:

```json
{
  "active_plan": "pro",
  ...
}
```

### Plans (threshold presets)

| Plan | Trigger | Use When |
|------|---------|----------|
| `free` | 72% | Anthropic Free tier |
| `pro` | 75% | Anthropic Pro ($20/mo) — **default** |
| `api_tier1` | 78% | Direct API, Tier 1 |
| `api_tier2` | 80% | API Tier 2+ |
| `custom` | set manually | Override `trigger_threshold` directly |

The threshold leaves enough context for Claude to generate all 3 docs before hitting the auto-compact at ~84%.

### Why These Numbers

From measuring real sessions:
- Claude Code auto-compacts at ~84% (`168,409 / 200,000` tokens)
- Pro plan default (75%) leaves ~18,000 tokens of runway
- At late-session growth rates (~1,500 tokens/turn), that's 10-12 turns of buffer

### Custom threshold

```json
{
  "active_plan": "custom",
  "plans": {
    "custom": {
      "trigger_threshold": 0.70,
      "note": "My custom setting"
    }
  }
}
```

### Context windows by model

All current Claude models use 200,000 tokens. If Anthropic changes this, update `models` in config.json.

## How Token Measurement Works

Each assistant message in the Claude Code transcript contains a `usage` field from the Anthropic API:

```json
{
  "usage": {
    "input_tokens": 1,
    "cache_read_input_tokens": 103100,
    "cache_creation_input_tokens": 1170,
    "output_tokens": 904
  }
}
```

**Total context used = `input_tokens + cache_read_input_tokens + cache_creation_input_tokens`**

The `input_tokens` on the *latest* assistant turn reflects the actual current context size (Claude sends the full conversation each call). This is the same number Claude Code uses for its `[X%]` status bar display.

## Uninstall

```bash
./uninstall.sh
```

## Files

```
context-guard/
├── install.sh
├── uninstall.sh
├── config.json                    # Plan thresholds, model windows
├── check_tokens.py                # Standalone token checker
├── hooks/
│   ├── stop_hook.py               # Fires after each turn — calculates %, sets flag
│   └── pre_tool_use_hook.py       # Fires before each tool — blocks if flagged
├── skills/
│   ├── session-save.md            # /session-save skill
│   └── tokens.md                  # /tokens skill
└── templates/
    ├── session_summary.md
    ├── next_steps.md
    └── resume_doc.md
```

## Requirements

- Claude Code (any version)
- Python 3 (pre-installed on macOS/Linux)
- No external Python packages required
