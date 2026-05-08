# context-guard

Automatic context window monitor for [Claude Code](https://claude.ai/code). Watches token usage every turn, warns you at a configurable threshold, and generates high-quality handoff documents before your context is lost.

## What It Does

1. **Monitors** — after every Claude turn, reads your session transcript and calculates exact token usage (`input + cache_read + cache_creation`)
2. **Warns** — when usage crosses your threshold, sets a flag
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
git clone https://github.com/traftonobrien/context-guard.git
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

Edit `~/.claude/context-guard/config.json` and set `active_plan` to match your subscription:

```json
{
  "active_plan": "pro"
}
```

### Plans

Pick the plan that matches your subscription. Each has a tuned threshold based on real session data.

| Plan Key | Label | Threshold | Context Window | Notes |
|----------|-------|-----------|----------------|-------|
| `free` | Claude.ai Free | 68% | 200k | 2–5 Claude Code prompts/5hr. Trigger early — recovery sessions are expensive. |
| `pro` | Claude.ai Pro ($20/mo) | **75%** | 200k | **Default.** 10–40 prompts/5hr. Doubled May 2026. |
| `pro_1m` | Claude.ai Pro — 1M beta | 75% | 1M | Use if your sessions aren't auto-compacting at ~168k tokens. |
| `max_5x` | Claude.ai Max 5x ($100/mo) | 78% | 200k | 50–200 prompts/5hr. Opus access included. |
| `max_5x_1m` | Claude.ai Max 5x — 1M beta | 78% | 1M | Max 5x with 1M context beta. |
| `max_20x` | Claude.ai Max 20x ($200/mo) | 80% | 200k | 200–800 prompts/5hr. No peak throttle. |
| `max_20x_1m` | Claude.ai Max 20x — 1M beta | 80% | 1M | Max 20x with 1M context beta. |
| `team` | Claude.ai Team ($25/seat) | 75% | 200k | ~56 msgs/5hr per seat. |
| `team_premium` | Claude.ai Team Premium ($125/seat) | 78% | 200k | ~280 msgs/5hr. Weekly caps apply. |
| `api_tier1` | Anthropic API Tier 1 | 75% | 200k | $5 deposit req. 50 RPM / 30k ITPM. |
| `api_tier2` | Anthropic API Tier 2 | 78% | 200k | $40 cumulative spend. 1k RPM / 450k ITPM. |
| `api_tier3` | Anthropic API Tier 3 | 80% | 200k | $200 cumulative spend. 2k RPM / 800k ITPM. |
| `api_tier4` | Anthropic API Tier 4+ | 82% | 200k | $400+ spend. 4k RPM / 2M ITPM. |
| `custom` | Custom | 75% | 200k | Edit `context_window` and `trigger_threshold` directly. |

### Why These Thresholds

From measuring real Claude Code sessions:
- Auto-compact fires at ~**84%** (~168k/200k tokens) — this is the hard wall
- Each late-session turn grows context by ~1,500–3,000 tokens
- The `/session-save` skill needs ~10,000–15,000 tokens to generate all 3 docs
- **Free** users get fewer sessions so threshold is lower — a failed save costs more
- **API Tier 4+** users have high rate limits and can afford to push closer to the wall

### The 1M Context Beta (Claude Code)

As of May 2026, Claude Code on Pro/Max/Team/Enterprise has a **1M token context window** (beta). If you're on this beta:
1. Your sessions will NOT auto-compact at ~168k tokens
2. Switch to `pro_1m`, `max_5x_1m`, or `max_20x_1m` in config
3. Threshold still triggers at 75%/78%/80% of the 1M window

**How to tell if you're on the 1M beta:** Sessions that previously compacted at ~168k tokens will now grow past 200k without compacting.

### Session Windows vs Context Windows

These are different things:

| Concept | What it is | Affects threshold? |
|---------|-----------|-------------------|
| **Context window** | Max tokens per API call (200k or 1M) | Yes — this is what we measure |
| **5-hour usage window** | How many messages/prompts per 5 hours | No — separate concern |
| **Weekly cap** | Added Aug 2025; affects <5% of users | No |

Context-guard monitors context window usage only. It does not track your 5-hour session budget.

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

The latest assistant turn's total reflects the actual current context size — Claude sends the full conversation on each API call. This matches what Claude Code displays in its `[X%]` status bar.

> Note: `output_tokens` is NOT included. Output tokens from the previous turn become input tokens on the next turn, so they're already counted.

## Custom Configuration

```json
{
  "active_plan": "custom",
  "plans": {
    "custom": {
      "label": "My Setup",
      "context_window": 200000,
      "trigger_threshold": 0.70,
      "note": "Override both context_window and trigger_threshold here"
    }
  }
}
```

## Uninstall

```bash
cd context-guard
./uninstall.sh
```

## Files

```
context-guard/
├── install.sh                     # Copies files + patches settings.json
├── uninstall.sh                   # Reverses install
├── config.json                    # Plan thresholds + context windows
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
