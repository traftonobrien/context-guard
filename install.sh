#!/bin/bash
# context-guard installer
# Installs hooks, config, skills, and patches ~/.claude/settings.json

set -e

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLAUDE_DIR="$HOME/.claude"
GUARD_DIR="$CLAUDE_DIR/context-guard"
SKILLS_DIR="$CLAUDE_DIR/skills"
SETTINGS="$CLAUDE_DIR/settings.json"

echo "context-guard installer"
echo "========================"

# --- Create directories
mkdir -p "$GUARD_DIR/hooks" "$GUARD_DIR/templates" "$SKILLS_DIR"

# --- Copy files
echo "→ Copying config and hooks..."
cp "$REPO_DIR/config.json"                      "$GUARD_DIR/config.json"
cp "$REPO_DIR/check_tokens.py"                  "$GUARD_DIR/check_tokens.py"
cp "$REPO_DIR/hooks/stop_hook.py"               "$GUARD_DIR/hooks/stop_hook.py"
cp "$REPO_DIR/hooks/pre_tool_use_hook.py"       "$GUARD_DIR/hooks/pre_tool_use_hook.py"
cp "$REPO_DIR/templates/session_summary.md"     "$GUARD_DIR/templates/session_summary.md"
cp "$REPO_DIR/templates/next_steps.md"          "$GUARD_DIR/templates/next_steps.md"
cp "$REPO_DIR/templates/resume_doc.md"          "$GUARD_DIR/templates/resume_doc.md"

echo "→ Copying skills..."
cp "$REPO_DIR/skills/session-save.md"           "$SKILLS_DIR/session-save.md"
cp "$REPO_DIR/skills/tokens.md"                 "$SKILLS_DIR/tokens.md"

chmod +x "$GUARD_DIR/hooks/stop_hook.py" "$GUARD_DIR/hooks/pre_tool_use_hook.py"

# --- Patch settings.json
echo "→ Patching $SETTINGS..."

if [ ! -f "$SETTINGS" ]; then
  echo '{}' > "$SETTINGS"
fi

# Use Python for safe JSON patching (no jq dependency)
python3 - "$SETTINGS" "$GUARD_DIR" <<'PYEOF'
import json
import sys

settings_path = sys.argv[1]
guard_dir = sys.argv[2]

with open(settings_path) as f:
    settings = json.load(f)

stop_hook = {
    "type": "command",
    "command": f"python3 \"{guard_dir}/hooks/stop_hook.py\"",
    "timeout": 10
}
pre_hook = {
    "type": "command",
    "command": f"python3 \"{guard_dir}/hooks/pre_tool_use_hook.py\"",
    "timeout": 5
}

hooks = settings.setdefault("hooks", {})

# Stop hook
stop_entries = hooks.setdefault("Stop", [])
existing_stop_cmds = [h["hooks"][0]["command"] for h in stop_entries if h.get("hooks")]
if stop_hook["command"] not in existing_stop_cmds:
    stop_entries.append({"hooks": [stop_hook]})

# PreToolUse hook
pre_entries = hooks.setdefault("PreToolUse", [])
existing_pre_cmds = [h["hooks"][0]["command"] for h in pre_entries if h.get("hooks")]
if pre_hook["command"] not in existing_pre_cmds:
    pre_entries.append({"hooks": [pre_hook]})

with open(settings_path, "w") as f:
    json.dump(settings, f, indent=2)

print("  settings.json patched successfully")
PYEOF

echo ""
echo "✓ context-guard installed"
echo ""
echo "Config:  $GUARD_DIR/config.json"
echo "Skills:  /tokens  and  /session-save  now available in Claude Code"
echo ""
echo "Default plan: pro (75% threshold)"
echo "To change: edit $GUARD_DIR/config.json → active_plan"
echo ""
echo "Plans available:"
echo "  free        → 72% threshold"
echo "  pro         → 75% threshold  (default)"
echo "  api_tier1   → 78% threshold"
echo "  api_tier2   → 80% threshold"
echo "  custom      → set trigger_threshold manually"
