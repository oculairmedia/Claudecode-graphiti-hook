# Claude Code Graphiti Hook - Enhanced Version with Session Summaries

This integration allows Claude Code to automatically send conversation data to a Graphiti knowledge graph, enabling AI agents to access and learn from Claude's development sessions WITH full conversation context and session summaries.

## Overview

The enhanced hook captures Claude Code tool usage events WITH conversation context and sends them to Graphiti, creating a searchable knowledge graph of:
- **User requests and Claude's responses** - Understanding the "why" behind actions
- **Files read and modified** - With context of what problem is being solved
- **Commands executed** - Including the purpose and expected outcome
- **Web searches performed** - With the research goal explained
- **Tasks created** - Including surrounding conversation for context
- **Notifications received** - With session activity summary
- **Session summaries** - Comprehensive analysis when conversations end

## Key Features

- **Full Conversation Context**: Captures not just WHAT Claude did, but WHY
- **Transcript Parsing**: Reads Claude's conversation transcripts to provide rich context
- **Session Tracking**: Links all actions to conversation sessions
- **Intent Understanding**: Other agents can understand the purpose behind actions
- **Contextual Search**: Search for actions based on user requests or goals
- **Session Summaries**: Automatic analysis and summarization when conversations end
- **Insight Extraction**: Identifies goals, problems solved, technologies used, and follow-up items

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

2. Copy the hook scripts:
```bash
cp graphiti_integration.py ~/.claude/hooks/
cp session_analyzer.py ~/.claude/hooks/
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

# Stop hook session summary test
python3 test_stop_hook.py
```

## How It Works

1. **Event Capture**: Claude Code triggers hooks on tool usage (PostToolUse), notifications, and session end (Stop)
2. **Transcript Reading**: The hook reads the conversation transcript to understand context
3. **Context Extraction**: Extracts user requests and Claude's responses around the tool use
4. **Data Enrichment**: Combines tool information with conversation context
5. **Session Analysis**: On Stop events, analyzes the full session to extract insights
6. **Message Formatting**: Creates comprehensive messages with full context and session summaries
7. **API Submission**: Messages are sent to Graphiti's `/messages` endpoint
8. **Knowledge Storage**: Graphiti stores rich contextual information in the knowledge graph

## Captured Events

### Tool Usage Events (with context)
- **Read**: File paths accessed + why the file was needed
- **Write/Edit/MultiEdit**: Files modified + what feature/fix was being implemented  
- **Bash**: Commands executed + their purpose and expected outcome
- **WebSearch**: Search queries + what information was being researched
- **WebFetch**: URLs accessed + why the content was needed
- **Task**: Task descriptions + the full agent prompt and context
- **Grep/Glob**: Search patterns + what was being looked for and why

### Session Events
- **Stop**: When conversation ends, creates comprehensive session summary including:
  - Main objectives and goals
  - Files modified during session
  - Problems solved
  - Key technical decisions
  - Technologies used
  - Session metrics (duration, success rate)
  - Learning outcomes
  - Follow-up items

### Excluded Tools
- TodoWrite (internal task management)
- exit_plan_mode (planning mode transitions)

## Data Format

### Tool Event Messages
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

### Session Summary Format
```json
{
  "messages": [{
    "content": "=== SESSION SUMMARY ===\nSession ID: abc-123\nTotal Messages: 45\n\n🎯 SESSION GOAL:\nPrimary goal: implement authentication system\n\n📁 FILES MODIFIED:\nTotal files: 3\n  • /auth/login.py (Write, Edit)\n  • /auth/middleware.py (Write)\n  • /tests/test_auth.py (Write)\n\n✅ PROBLEMS SOLVED:\n  • Solution achieved: Fixed authentication token validation...\n\n🛠️ TECHNOLOGIES USED:\n  Python, FastAPI, JWT\n\n📊 SESSION METRICS:\n  Duration: 35.2 minutes\n  Tools used: 15\n  Success rate: 93.3%\n\n🔜 FOLLOW-UP ITEMS:\n  • Add rate limiting to authentication endpoints\n  • Implement refresh token mechanism",
    "role_type": "system",
    "role": "claude_session_summarizer",
    "name": "Claude_Session_Summary_2025-01-08T03:45:00",
    "source_description": "Claude Code session summary with insights",
    "timestamp": "2025-01-08T03:45:00.123456"
  }],
  "group_id": "claude_conversations"
}
```

## Querying Data

To search for Claude's activities in Graphiti:

```bash
# Search for specific activities
curl -X POST "http://192.168.50.90:8001/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "authentication implementation",
    "max_facts": 20,
    "group_ids": ["claude_conversations"]
  }'

# Search for session summaries
curl -X POST "http://192.168.50.90:8001/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "SESSION SUMMARY",
    "max_facts": 10,
    "group_ids": ["claude_conversations"]
  }'
```

## Troubleshooting

1. **Check hook execution**: Look for logs in Claude Code output
2. **Verify Graphiti connectivity**: `curl http://192.168.50.90:8001/health`
3. **Test manually**: Run `python3 test_hook.py` to verify the integration
4. **Check permissions**: Ensure hook script is executable
5. **Session summaries not appearing**: Ensure Stop hook is configured in settings.json

## Contributing

Issues and pull requests are welcome at: https://github.com/oculairmedia/Claudecode-graphiti-hook

## License

MIT License - See LICENSE file for details