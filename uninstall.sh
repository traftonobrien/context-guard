#!/bin/bash
# context-guard uninstaller

set -e

CLAUDE_DIR="$HOME/.claude"
GUARD_DIR="$CLAUDE_DIR/context-guard"
SETTINGS="$CLAUDE_DIR/settings.json"

echo "context-guard uninstaller"
echo "========================="

# Remove hooks from settings.json
if [ -f "$SETTINGS" ]; then
  echo "→ Removing hooks from settings.json..."
  python3 - "$SETTINGS" "$GUARD_DIR" <<'PYEOF'
import json, sys

settings_path = sys.argv[1]
guard_dir = sys.argv[2]

with open(settings_path) as f:
    settings = json.load(f)

hooks = settings.get("hooks", {})

for hook_type in ("Stop", "PreToolUse"):
    if hook_type in hooks:
        hooks[hook_type] = [
            entry for entry in hooks[hook_type]
            if not any(guard_dir in h.get("command", "") for h in entry.get("hooks", []))
        ]
        if not hooks[hook_type]:
            del hooks[hook_type]

with open(settings_path, "w") as f:
    json.dump(settings, f, indent=2)

print("  hooks removed from settings.json")
PYEOF
fi

# Remove files
echo "→ Removing ~/.claude/context-guard/ ..."
rm -rf "$GUARD_DIR"

echo "→ Removing skills..."
rm -f "$CLAUDE_DIR/skills/session-save.md"
rm -f "$CLAUDE_DIR/skills/tokens.md"

echo "→ Removing flag file if present..."
rm -f /tmp/context-guard-flag.json

echo ""
echo "✓ context-guard uninstalled"
