# Claude Code Graphiti Hook

This integration allows Claude Code to automatically send conversation data to a Graphiti knowledge graph, enabling AI agents to access and learn from Claude's development sessions.

## Overview

The hook captures Claude Code tool usage events and sends them to Graphiti, creating a searchable knowledge graph of:
- Files read and modified
- Commands executed
- Web searches performed
- Tasks created
- Notifications received

## Prerequisites

- Claude Code installed and configured
- Graphiti instance running (default: `http://192.168.50.90:8001`)
- Python 3.x with `requests` library

## Installation

### Automated Installation

Run the installation script:

```bash
curl -sSL https://raw.githubusercontent.com/oculairmedia/Claudecode-graphiti-hook/main/install.sh | bash
```

### Manual Installation

1. Create the hooks directory:
```bash
mkdir -p ~/.claude/hooks
```

2. Copy the hook script:
```bash
cp graphiti_integration.py ~/.claude/hooks/
chmod +x ~/.claude/hooks/graphiti_integration.py
```

3. Update Claude settings (`~/.claude/settings.json`):
```json
{
  "model": "opus",
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
```

## Configuration

Environment variables:
- `GRAPHITI_URL`: Graphiti API endpoint (default: `http://192.168.50.90:8001`)
- `GRAPHITI_TIMEOUT`: Request timeout in seconds (default: 30)

## Testing

Run the test script to verify the integration:

```bash
python3 test_hook.py
```

## How It Works

1. **Event Capture**: Claude Code triggers hooks on tool usage (PostToolUse) and notifications
2. **Data Extraction**: The hook extracts relevant information based on the tool type
3. **Message Formatting**: Events are formatted as Graphiti messages with proper metadata
4. **API Submission**: Messages are sent to Graphiti's `/messages` endpoint
5. **Knowledge Storage**: Graphiti processes and stores the information in the knowledge graph

## Captured Events

### Tool Usage Events
- **Read**: File paths accessed
- **Write/Edit/MultiEdit**: Files modified
- **Bash**: Commands executed
- **WebSearch**: Search queries
- **WebFetch**: URLs accessed
- **Task**: Task descriptions

### Excluded Tools
- TodoWrite (internal task management)
- exit_plan_mode (planning mode transitions)

## Data Format

Messages are sent to Graphiti with the following structure:
```json
{
  "messages": [{
    "content": "Claude executed command: ls -la",
    "role_type": "system",
    "role": "claude_code",
    "name": "Claude_Bash_2025-01-08T02:12:32",
    "source_description": "Claude Code conversation",
    "timestamp": "2025-01-08T02:12:32.123456"
  }],
  "group_id": "claude_conversations"
}
```

## Querying Data

To search for Claude's activities in Graphiti:

```bash
curl -X POST "http://192.168.50.90:8001/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Claude",
    "max_facts": 20,
    "group_ids": ["claude_conversations"]
  }'
```

## Troubleshooting

1. **Check hook execution**: Look for logs in Claude Code output
2. **Verify Graphiti connectivity**: `curl http://192.168.50.90:8001/health`
3. **Test manually**: Run `python3 test_hook.py` to verify the integration
4. **Check permissions**: Ensure hook script is executable

## Contributing

Issues and pull requests are welcome at: https://github.com/oculairmedia/Claudecode-graphiti-hook

## License

MIT License - See LICENSE file for details