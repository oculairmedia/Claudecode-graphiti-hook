#!/usr/bin/env python3
"""
Claude to Graphiti Integration Hook - Enhanced Version
Captures Claude conversation data including full context and sends it to Graphiti knowledge graph
"""

import json
import sys
import os
import requests
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import logging
import uuid

# Import session analyzer
try:
    from session_analyzer import SessionAnalyzer
except ImportError:
    # Fallback if session_analyzer is not available
    class SessionAnalyzer:
        def analyze_session(self, messages):
            return {"error": "SessionAnalyzer not available"}

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Graphiti configuration
GRAPHITI_URL = os.getenv("GRAPHITI_URL", "http://192.168.50.90:8001")
GRAPHITI_TIMEOUT = int(os.getenv("GRAPHITI_TIMEOUT", "30"))
CLAUDE_GROUP_ID = "claude_conversations"  # Group ID for Claude conversations

class TranscriptParser:
    """Parse Claude transcript files to extract conversation context"""
    
    def parse_transcript(self, transcript_path: str) -> List[Dict]:
        """Parse JSONL transcript file and extract messages"""
        messages = []
        full_path = os.path.expanduser(transcript_path)
        
        if not os.path.exists(full_path):
            logger.warning(f"Transcript file not found: {full_path}")
            return messages
            
        try:
            with open(full_path, 'r') as f:
                for line in f:
                    if line.strip():
                        try:
                            entry = json.loads(line)
                            self._process_entry(entry, messages)
                        except json.JSONDecodeError:
                            continue
                            
        except Exception as e:
            logger.error(f"Error reading transcript: {e}")
            
        return messages
        
    def _process_entry(self, entry: Dict, messages: List[Dict]) -> None:
        """Process a single transcript entry"""
        entry_type = entry.get('type', '')
        
        if entry_type == 'user' and 'message' in entry:
            messages.append({
                'type': 'user',
                'content': entry['message'].get('content', ''),
                'timestamp': entry.get('timestamp', ''),
                'uuid': entry.get('uuid', ''),
                'sessionId': entry.get('sessionId', '')
            })
        elif entry_type == 'assistant' and 'message' in entry:
            messages.append({
                'type': 'assistant', 
                'content': entry['message'].get('content', ''),
                'timestamp': entry.get('timestamp', ''),
                'uuid': entry.get('uuid', ''),
                'sessionId': entry.get('sessionId', '')
            })
        elif entry_type == 'tool_use':
            messages.append({
                'type': 'tool_use',
                'tool': entry.get('toolName', ''),
                'input': entry.get('input', {}),
                'timestamp': entry.get('timestamp', ''),
                'uuid': entry.get('uuid', ''),
                'sessionId': entry.get('sessionId', '')
            })
        elif entry_type == 'tool_result':
            messages.append({
                'type': 'tool_result',
                'tool': entry.get('toolName', ''),
                'output': str(entry.get('output', ''))[:500],  # Truncate long outputs
                'error': entry.get('isError', False),
                'timestamp': entry.get('timestamp', ''),
                'uuid': entry.get('uuid', ''),
                'sessionId': entry.get('sessionId', '')
            })

class GraphitiIntegration:
    def __init__(self):
        self.base_url = GRAPHITI_URL
        self.session = requests.Session()
        self.parser = TranscriptParser()
        self.analyzer = SessionAnalyzer()
        
    def process_tool_event(self, event_data: Dict) -> None:
        """Process Claude tool events and send to Graphiti with conversation context"""
        try:
            # Extract relevant information
            tool_name = event_data.get("tool_name", "")
            timestamp = event_data.get("timestamp", datetime.now().isoformat())
            transcript_path = event_data.get("transcript_path", "")
            session_id = event_data.get("session_id", "")
            
            # Skip certain tool events we don't want to track
            if tool_name in ["TodoWrite", "exit_plan_mode"]:
                return
                
            # Get conversation context from transcript
            conversation_context = self._get_conversation_context(
                transcript_path, 
                session_id,
                tool_name,
                event_data
            )
            
            # Create and send message with context
            message = self._create_contextual_message(
                event_data, 
                tool_name, 
                timestamp,
                conversation_context
            )
            
            if message:
                self._send_to_graphiti(message)
                
        except Exception as e:
            logger.error(f"Error processing tool event: {e}")
            
    def _get_conversation_context(self, transcript_path: str, session_id: str, 
                                  tool_name: str, event_data: Dict) -> Dict:
        """Extract conversation context from transcript"""
        try:
            if not transcript_path:
                return {"error": "No transcript path provided"}
                
            # Parse transcript
            messages = self.parser.parse_transcript(transcript_path)
            
            if not messages:
                return {"error": "No messages found in transcript"}
                
            # Get recent conversation context
            recent_messages = messages[-20:]  # Last 20 messages
            
            # Find the most recent user request before this tool
            last_user_request = None
            last_assistant_response = None
            
            for msg in reversed(recent_messages):
                if msg['type'] == 'user' and not last_user_request:
                    last_user_request = msg['content']
                elif msg['type'] == 'assistant' and not last_assistant_response:
                    last_assistant_response = msg['content'][:500]  # Truncate
                    
                if last_user_request and last_assistant_response:
                    break
                    
            # Get conversation summary
            user_messages = [m for m in recent_messages if m['type'] == 'user']
            assistant_messages = [m for m in recent_messages if m['type'] == 'assistant']
            tool_uses = [m for m in recent_messages if m['type'] == 'tool_use']
            
            return {
                "last_user_request": last_user_request or "No recent user request found",
                "last_assistant_response": last_assistant_response or "No recent response found",
                "recent_context": {
                    "user_message_count": len(user_messages),
                    "assistant_message_count": len(assistant_messages),
                    "tool_use_count": len(tool_uses),
                    "session_id": session_id
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting conversation context: {e}")
            return {"error": str(e)}
            
    def _create_contextual_message(self, event_data: Dict, tool_name: str, 
                                   timestamp: str, context: Dict) -> Optional[Dict]:
        """Create a message with conversation context for Graphiti"""
        try:
            # Extract tool-specific information
            tool_info = self._extract_tool_info(event_data, tool_name)
            
            # Build comprehensive content
            content_parts = []
            
            # Add user request context
            if context.get("last_user_request"):
                content_parts.append(f"User request: {context['last_user_request']}")
                
            # Add Claude's response context
            if context.get("last_assistant_response"):
                content_parts.append(f"Claude's context: {context['last_assistant_response']}")
                
            # Add tool action
            content_parts.append(f"Action: {tool_info}")
            
            # Add context summary
            if "recent_context" in context:
                ctx = context["recent_context"]
                content_parts.append(
                    f"Session context: {ctx['user_message_count']} user messages, "
                    f"{ctx['assistant_message_count']} assistant messages, "
                    f"{ctx['tool_use_count']} tool uses"
                )
                
            content = "\n\n".join(content_parts)
            
            # Create Graphiti message
            message = {
                "content": content,
                "name": f"Claude_{tool_name}_{timestamp}",
                "role_type": "system",
                "role": "claude_code",
                "timestamp": timestamp,
                "source_description": "Claude Code conversation with context",
                "group_id": CLAUDE_GROUP_ID,
                "metadata": {
                    "tool_name": tool_name,
                    "session_id": context.get("recent_context", {}).get("session_id", ""),
                    "has_context": True
                }
            }
            
            return message
            
        except Exception as e:
            logger.error(f"Error creating contextual message: {e}")
            return None
            
    def _extract_tool_info(self, event_data: Dict, tool_name: str) -> str:
        """Extract tool-specific information"""
        try:
            tool_input = event_data.get("tool_input", {})
            
            if tool_name == "Read":
                file_path = tool_input.get("file_path", "")
                return f"Claude read file: {file_path}"
                
            elif tool_name in ["Write", "Edit", "MultiEdit"]:
                file_path = tool_input.get("file_path", "")
                return f"Claude modified file: {file_path}"
                
            elif tool_name == "Bash":
                command = tool_input.get("command", "")
                description = tool_input.get("description", "")
                return f"Claude executed command: {command} ({description})"
                
            elif tool_name == "WebSearch":
                query = tool_input.get("query", "")
                return f"Claude searched web for: {query}"
                
            elif tool_name == "WebFetch":
                url = tool_input.get("url", "")
                prompt = tool_input.get("prompt", "")
                return f"Claude fetched URL: {url} (purpose: {prompt})"
                
            elif tool_name == "Task":
                description = tool_input.get("description", "")
                prompt = tool_input.get("prompt", "")[:200]
                return f"Claude created task: {description} - {prompt}"
                
            elif tool_name == "Grep":
                pattern = tool_input.get("pattern", "")
                path = tool_input.get("path", ".")
                return f"Claude searched for pattern '{pattern}' in {path}"
                
            elif tool_name == "Glob":
                pattern = tool_input.get("pattern", "")
                path = tool_input.get("path", ".")
                return f"Claude searched for files matching '{pattern}' in {path}"
                
            else:
                # Generic message for other tools
                return f"Claude used {tool_name} tool: {json.dumps(tool_input)[:200]}"
                
        except Exception as e:
            logger.error(f"Error extracting tool info: {e}")
            return f"Claude used {tool_name} tool"
            
    def _send_to_graphiti(self, message: Dict) -> None:
        """Send message to Graphiti API"""
        try:
            endpoint = f"{self.base_url}/messages"
            
            # Format for messages endpoint
            payload = {
                "messages": [{
                    "content": message.get("content", ""),
                    "role_type": message.get("role_type", "system"),
                    "role": message.get("role", "claude_code"),
                    "name": message.get("name", f"Claude_{datetime.now().isoformat()}"),
                    "source_description": message.get("source_description", "Claude Code"),
                    "timestamp": message.get("timestamp", datetime.now().isoformat())
                }],
                "group_id": CLAUDE_GROUP_ID
            }
            
            response = self.session.post(
                endpoint,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=GRAPHITI_TIMEOUT
            )
            
            if response.status_code in [200, 202]:
                logger.info(f"Successfully sent to Graphiti: {message['name']}")
            else:
                logger.error(f"Failed to send to Graphiti: {response.status_code} - {response.text}")
                
        except requests.exceptions.Timeout:
            logger.error("Timeout sending to Graphiti")
        except Exception as e:
            logger.error(f"Error sending to Graphiti: {e}")
            
    def process_notification(self, notification_data: Dict) -> None:
        """Process Claude notifications"""
        try:
            message = notification_data.get("message", "")
            timestamp = notification_data.get("timestamp", datetime.now().isoformat())
            transcript_path = notification_data.get("transcript_path", "")
            
            # Get minimal context for notifications
            context = {"notification": True}
            if transcript_path:
                messages = self.parser.parse_transcript(transcript_path)
                if messages:
                    # Just get counts for notifications
                    context["message_count"] = len(messages)
            
            # Create notification message
            graphiti_message = {
                "content": f"Claude notification: {message} (Total messages in session: {context.get('message_count', 'unknown')})",
                "name": f"Claude_Notification_{timestamp}",
                "role_type": "system",
                "role": "claude_code",
                "timestamp": timestamp,
                "source_description": "Claude Code notification",
                "group_id": CLAUDE_GROUP_ID
            }
            
            self._send_to_graphiti(graphiti_message)
            
        except Exception as e:
            logger.error(f"Error processing notification: {e}")
            
    def process_stop_event(self, stop_data: Dict) -> None:
        """Process session stop events and create comprehensive summary"""
        try:
            transcript_path = stop_data.get("transcript_path", "")
            session_id = stop_data.get("session_id", "")
            timestamp = datetime.now().isoformat()
            
            if not transcript_path:
                logger.warning("No transcript path for session summary")
                return
                
            # Parse full transcript
            messages = self.parser.parse_transcript(transcript_path)
            if not messages:
                logger.warning("No messages found for session summary")
                return
                
            # Analyze session
            analysis = self.analyzer.analyze_session(messages)
            
            # Create comprehensive session summary
            summary_content = self._create_session_summary(analysis, session_id, len(messages))
            
            # Send to Graphiti
            summary_message = {
                "content": summary_content,
                "name": f"Claude_Session_Summary_{timestamp}",
                "role_type": "system",
                "role": "claude_session_summarizer",
                "timestamp": timestamp,
                "source_description": "Claude Code session summary with insights",
                "group_id": CLAUDE_GROUP_ID,
                "metadata": {
                    "session_id": session_id,
                    "message_count": len(messages),
                    "is_summary": True,
                    "analysis": analysis
                }
            }
            
            self._send_to_graphiti(summary_message)
            logger.info(f"Session summary sent for session {session_id}")
            
        except Exception as e:
            logger.error(f"Error processing stop event: {e}")
            
    def _create_session_summary(self, analysis: Dict, session_id: str, message_count: int) -> str:
        """Create a formatted session summary"""
        try:
            summary_parts = [
                f"=== SESSION SUMMARY ===",
                f"Session ID: {session_id}",
                f"Total Messages: {message_count}",
                ""
            ]
            
            # Add main objective
            if analysis.get("session_goal"):
                summary_parts.extend([
                    "🎯 SESSION GOAL:",
                    analysis["session_goal"],
                    ""
                ])
            
            # Add files modified
            files_modified = analysis.get("files_modified", [])
            if files_modified:
                summary_parts.extend([
                    "📁 FILES MODIFIED:",
                    f"Total files: {len(files_modified)}"
                ])
                for file_info in files_modified[:5]:  # Show top 5
                    operations = ", ".join(set(file_info.get("operations", [])))
                    summary_parts.append(f"  • {file_info.get('file', 'Unknown')} ({operations})")
                if len(files_modified) > 5:
                    summary_parts.append(f"  ... and {len(files_modified) - 5} more files")
                summary_parts.append("")
            
            # Add problems solved
            problems_solved = analysis.get("problems_solved", [])
            if problems_solved:
                summary_parts.extend([
                    "✅ PROBLEMS SOLVED:",
                ])
                for solution in problems_solved[:3]:
                    summary_parts.append(f"  • {solution}")
                summary_parts.append("")
            
            # Add key decisions
            decisions = analysis.get("key_decisions", [])
            if decisions:
                summary_parts.extend([
                    "🔄 KEY DECISIONS:",
                ])
                for decision in decisions[:3]:
                    summary_parts.append(f"  • {decision}")
                summary_parts.append("")
            
            # Add technologies used
            technologies = analysis.get("technologies_used", [])
            if technologies:
                summary_parts.extend([
                    "🛠️ TECHNOLOGIES USED:",
                    f"  {', '.join(technologies)}",
                    ""
                ])
            
            # Add session metrics
            metrics = analysis.get("session_metrics", {})
            if metrics:
                summary_parts.extend([
                    "📊 SESSION METRICS:",
                    f"  Duration: {metrics.get('session_duration', 'Unknown')}",
                    f"  Tools used: {metrics.get('tools_used', 0)}",
                    f"  Success rate: {metrics.get('success_rate', 'N/A')}",
                    ""
                ])
            
            # Add learnings
            learnings = analysis.get("learning_outcomes", [])
            if learnings:
                summary_parts.extend([
                    "💡 KEY LEARNINGS:",
                ])
                for learning in learnings:
                    summary_parts.append(f"  • {learning}")
                summary_parts.append("")
            
            # Add follow-ups
            follow_ups = analysis.get("follow_up_items", [])
            if follow_ups:
                summary_parts.extend([
                    "🔜 FOLLOW-UP ITEMS:",
                ])
                for follow_up in follow_ups:
                    summary_parts.append(f"  • {follow_up}")
                summary_parts.append("")
            
            return "\n".join(summary_parts)
            
        except Exception as e:
            logger.error(f"Error creating session summary: {e}")
            return f"Session summary error: {str(e)}"

def main():
    """Main entry point for hook script"""
    try:
        # Read event data from stdin
        event_json = sys.stdin.read()
        event_data = json.loads(event_json)
        
        # Get event type
        event_type = event_data.get("hook_event_name", "")
        
        # Initialize integration
        integration = GraphitiIntegration()
        
        # Process based on event type
        if event_type == "PostToolUse":
            integration.process_tool_event(event_data)
        elif event_type == "Notification":
            integration.process_notification(event_data)
        elif event_type == "Stop":
            integration.process_stop_event(event_data)
            
    except Exception as e:
        logger.error(f"Hook error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()