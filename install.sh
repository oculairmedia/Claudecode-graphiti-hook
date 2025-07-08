#!/bin/bash
# Claude Code Graphiti Hook Installation Script

set -e

echo "Installing Claude Code Graphiti Hook..."

# Check if Claude is installed
if [ ! -d "$HOME/.claude" ]; then
    echo "Error: Claude directory not found at ~/.claude"
    echo "Please ensure Claude Code is installed first."
    exit 1
fi

# Create hooks directory
mkdir -p "$HOME/.claude/hooks"

# Download the hook script
echo "Downloading hook script..."
curl -sSL https://raw.githubusercontent.com/oculairmedia/Claudecode-graphiti-hook/main/graphiti_integration.py \
    -o "$HOME/.claude/hooks/graphiti_integration.py"

# Make it executable
chmod +x "$HOME/.claude/hooks/graphiti_integration.py"

# Check if settings.json exists
SETTINGS_FILE="$HOME/.claude/settings.json"
if [ ! -f "$SETTINGS_FILE" ]; then
    echo "Creating settings.json..."
    cat > "$SETTINGS_FILE" <<EOF
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.claude/hooks/graphiti_integration.py"
          }
        ]
      }
    ],
    "Notification": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.claude/hooks/graphiti_integration.py"
          }
        ]
      }
    ]
  }
}
EOF
else
    echo "Warning: settings.json already exists"
    echo "Please manually add the hooks configuration to: $SETTINGS_FILE"
    echo ""
    echo "Required configuration:"
    cat <<EOF
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.claude/hooks/graphiti_integration.py"
          }
        ]
      }
    ],
    "Notification": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.claude/hooks/graphiti_integration.py"
          }
        ]
      }
    ]
  }
}
EOF
fi

# Download test script
echo "Downloading test script..."
curl -sSL https://raw.githubusercontent.com/oculairmedia/Claudecode-graphiti-hook/main/test_hook.py \
    -o "$HOME/.claude/hooks/test_hook.py"
chmod +x "$HOME/.claude/hooks/test_hook.py"

echo ""
echo "Installation complete!"
echo ""
echo "Configuration:"
echo "- Hook script: ~/.claude/hooks/graphiti_integration.py"
echo "- Test script: ~/.claude/hooks/test_hook.py"
echo ""
echo "Environment variables (optional):"
echo "- GRAPHITI_URL: Graphiti API endpoint (default: http://192.168.50.90:8001)"
echo "- GRAPHITI_TIMEOUT: Request timeout in seconds (default: 30)"
echo ""
echo "To test the installation, run:"
echo "  python3 ~/.claude/hooks/test_hook.py"
echo ""