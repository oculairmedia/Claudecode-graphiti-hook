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

# Download the hook scripts
echo "Downloading hook script..."
curl -sSL https://raw.githubusercontent.com/oculairmedia/Claudecode-graphiti-hook/main/graphiti_integration.py \
    -o "$HOME/.claude/hooks/graphiti_integration.py"

echo "Downloading session analyzer..."
curl -sSL https://raw.githubusercontent.com/oculairmedia/Claudecode-graphiti-hook/main/session_analyzer.py \
    -o "$HOME/.claude/hooks/session_analyzer.py"

# Make them executable
chmod +x "$HOME/.claude/hooks/graphiti_integration.py"
chmod +x "$HOME/.claude/hooks/session_analyzer.py"

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
    ],
    "Stop": [
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
    ],
    "Stop": [
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

# Download test scripts
echo "Downloading test scripts..."
curl -sSL https://raw.githubusercontent.com/oculairmedia/Claudecode-graphiti-hook/main/test_hook.py \
    -o "$HOME/.claude/hooks/test_hook.py"
curl -sSL https://raw.githubusercontent.com/oculairmedia/Claudecode-graphiti-hook/main/test_enhanced_hook.py \
    -o "$HOME/.claude/hooks/test_enhanced_hook.py"
curl -sSL https://raw.githubusercontent.com/oculairmedia/Claudecode-graphiti-hook/main/test_stop_hook.py \
    -o "$HOME/.claude/hooks/test_stop_hook.py"

chmod +x "$HOME/.claude/hooks/test_hook.py"
chmod +x "$HOME/.claude/hooks/test_enhanced_hook.py"
chmod +x "$HOME/.claude/hooks/test_stop_hook.py"

echo ""
echo "Installation complete!"
echo ""
echo "Configuration:"
echo "- Hook script: ~/.claude/hooks/graphiti_integration.py"
echo "- Session analyzer: ~/.claude/hooks/session_analyzer.py"
echo "- Test scripts: ~/.claude/hooks/test_*.py"
echo ""
echo "Environment variables (optional):"
echo "- GRAPHITI_URL: Graphiti API endpoint (default: http://192.168.50.90:8001)"
echo "- GRAPHITI_TIMEOUT: Request timeout in seconds (default: 30)"
echo ""
echo "To test the installation, run:"
echo "  python3 ~/.claude/hooks/test_hook.py"
echo "  python3 ~/.claude/hooks/test_enhanced_hook.py"
echo "  python3 ~/.claude/hooks/test_stop_hook.py"
echo ""