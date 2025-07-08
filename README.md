# Claude Code Graphiti Hook - Enhanced Version

This integration allows Claude Code to automatically send conversation data to a Graphiti knowledge graph, enabling AI agents to access and learn from Claude's development sessions WITH full conversation context.

## Overview

The enhanced hook captures Claude Code tool usage events WITH conversation context and sends them to Graphiti, creating a searchable knowledge graph of:
- **User requests and Claude's responses** - Understanding the "why" behind actions
- **Files read and modified** - With context of what problem is being solved
- **Commands executed** - Including the purpose and expected outcome
- **Web searches performed** - With the research goal explained
- **Tasks created** - Including surrounding conversation for context
- **Notifications received** - With session activity summary

## Key Features

- **Full Conversation Context**: Captures not just WHAT Claude did, but WHY
- **Transcript Parsing**: Reads Claude's conversation transcripts to provide rich context
- **Session Tracking**: Links all actions to conversation sessions
- **Intent Understanding**: Other agents can understand the purpose behind actions
- **Contextual Search**: Search for actions based on user requests or goals

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

Run the test scripts to verify the integration:

```bash
# Basic functionality test
python3 test_hook.py

# Enhanced context test
python3 test_enhanced_hook.py
```

## How It Works

1. **Event Capture**: Claude Code triggers hooks on tool usage (PostToolUse) and notifications
2. **Transcript Reading**: The hook reads the conversation transcript to understand context
3. **Context Extraction**: Extracts user requests and Claude's responses around the tool use
4. **Data Enrichment**: Combines tool information with conversation context
5. **Message Formatting**: Creates comprehensive messages with full context
6. **API Submission**: Messages are sent to Graphiti's `/messages` endpoint
7. **Knowledge Storage**: Graphiti stores rich contextual information in the knowledge graph

## Captured Events

### Tool Usage Events (with context)
- **Read**: File paths accessed + why the file was needed
- **Write/Edit/MultiEdit**: Files modified + what feature/fix was being implemented  
- **Bash**: Commands executed + their purpose and expected outcome
- **WebSearch**: Search queries + what information was being researched
- **WebFetch**: URLs accessed + why the content was needed
- **Task**: Task descriptions + the full agent prompt and context
- **Grep/Glob**: Search patterns + what was being looked for and why

### Excluded Tools
- TodoWrite (internal task management)
- exit_plan_mode (planning mode transitions)

## Data Format

Messages are sent to Graphiti with enhanced context:
```json
{
  "messages": [{
    "content": "User request: Help me find all Python files in the project\n\nClaude's context: I'll help you find all Python files in your project. Let me search for them using the file pattern matching tool...\n\nAction: Claude searched for files matching '**/*.py' in .\n\nSession context: 5 user messages, 4 assistant messages, 3 tool uses",
    "role_type": "system",
    "role": "claude_code",
    "name": "Claude_Glob_2025-01-08T02:12:32",
    "source_description": "Claude Code conversation with context",
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