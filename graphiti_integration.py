#!/usr/bin/env python3
"""
Claude to Graphiti Integration Hook
Captures Claude conversation data and sends it to Graphiti knowledge graph
Uses existing Graphiti API patterns from the codebase
"""

import json
import sys
import os
import requests
from datetime import datetime
from typing import Dict, List, Optional
import logging
import uuid

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

class GraphitiIntegration:
    def __init__(self):
        self.base_url = GRAPHITI_URL
        self.session = requests.Session()
        
    def process_tool_event(self, event_data: Dict) -> None:
        """Process Claude tool events and send to Graphiti"""
        try:
            # Extract relevant information
            tool_name = event_data.get("tool", "")
            tool_type = event_data.get("type", "")
            timestamp = event_data.get("timestamp", datetime.now().isoformat())
            
            # Skip certain tool events we don't want to track
            if tool_name in ["TodoWrite", "exit_plan_mode"]:
                return
                
            # Prepare message for Graphiti
            message = self._create_message(event_data, tool_name, timestamp)
            
            # Send to Graphiti
            if message:
                self._send_to_graphiti(message)
                
        except Exception as e:
            logger.error(f"Error processing tool event: {e}")
            
    def _create_message(self, event_data: Dict, tool_name: str, timestamp: str) -> Optional[Dict]:
        """Create a message formatted for Graphiti ingestion"""
        try:
            # Extract content based on tool type
            content = ""
            
            if tool_name == "Read":
                file_path = event_data.get("parameters", {}).get("file_path", "")
                content = f"Claude read file: {file_path}"
                
            elif tool_name == "Write" or tool_name == "Edit" or tool_name == "MultiEdit":
                file_path = event_data.get("parameters", {}).get("file_path", "")
                content = f"Claude modified file: {file_path}"
                
            elif tool_name == "Bash":
                command = event_data.get("parameters", {}).get("command", "")
                content = f"Claude executed command: {command}"
                
            elif tool_name == "WebSearch":
                query = event_data.get("parameters", {}).get("query", "")
                content = f"Claude searched web for: {query}"
                
            elif tool_name == "WebFetch":
                url = event_data.get("parameters", {}).get("url", "")
                content = f"Claude fetched URL: {url}"
                
            elif tool_name == "Task":
                description = event_data.get("parameters", {}).get("description", "")
                content = f"Claude created task: {description}"
                
            else:
                # Generic message for other tools
                params = event_data.get("parameters", {})
                content = f"Claude used {tool_name} tool with parameters: {json.dumps(params, indent=2)}"
                
            if not content:
                return None
                
            # Create Graphiti message
            message = {
                "content": content,
                "name": f"Claude_{tool_name}_{timestamp}",
                "role_type": "system",
                "role": "claude_code",
                "timestamp": timestamp,
                "source_description": "Claude Code conversation",
                "group_id": CLAUDE_GROUP_ID  # Group all Claude conversations
            }
            
            return message
            
        except Exception as e:
            logger.error(f"Error creating message: {e}")
            return None
            
    def _send_to_graphiti(self, message: Dict) -> None:
        """Send message to Graphiti API using the messages endpoint"""
        try:
            # Use the messages endpoint as shown in the API documentation
            endpoint = f"{self.base_url}/messages"
            
            # Format the message for the messages endpoint - expects a dict with 'messages' key
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
            
            if response.status_code in [200, 202]:  # 202 = Accepted for async processing
                logger.info(f"Successfully sent to Graphiti: {message['name']}")
            else:
                logger.error(f"Failed to send to Graphiti: {response.status_code} - {response.text}")
                # Try alternative endpoint if messages endpoint fails
                self._try_alternative_endpoint(message)
                
        except requests.exceptions.Timeout:
            logger.error("Timeout sending to Graphiti")
        except Exception as e:
            logger.error(f"Error sending to Graphiti: {e}")
            
    def _try_alternative_endpoint(self, message: Dict) -> None:
        """Try alternative add-memory endpoint if messages endpoint fails"""
        try:
            endpoint = f"{self.base_url}/add-memory"
            
            payload = {
                "messages": [{
                    "role": message.get("role_type", "system"),
                    "content": message.get("content", ""),
                    "metadata": {
                        "agent_id": CLAUDE_GROUP_ID,
                        "timestamp": message.get("timestamp", datetime.now().isoformat()),
                        "source": message.get("source_description", "Claude Code"),
                        "name": message.get("name", "")
                    }
                }]
            }
            
            response = self.session.post(
                endpoint,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=GRAPHITI_TIMEOUT
            )
            
            if response.status_code == 200:
                logger.info(f"Successfully sent to Graphiti via add-memory: {message['name']}")
            else:
                logger.error(f"Alternative endpoint also failed: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Error with alternative endpoint: {e}")
            
    def process_notification(self, notification_data: Dict) -> None:
        """Process Claude notifications and important messages"""
        try:
            message = notification_data.get("message", "")
            timestamp = notification_data.get("timestamp", datetime.now().isoformat())
            
            # Create notification message
            graphiti_message = {
                "content": f"Claude notification: {message}",
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
            
    def search_related_context(self, query: str, max_nodes: int = 5, max_facts: int = 10) -> Dict:
        """Search for related context in Graphiti (for future use)"""
        try:
            # Search nodes
            nodes_response = self.session.post(
                f"{self.base_url}/search/nodes",
                json={
                    "query": query,
                    "max_nodes": max_nodes,
                    "group_ids": [CLAUDE_GROUP_ID]
                },
                headers={"Content-Type": "application/json"},
                timeout=GRAPHITI_TIMEOUT
            )
            
            # Search facts
            facts_response = self.session.post(
                f"{self.base_url}/search",
                json={
                    "query": query,
                    "max_facts": max_facts,
                    "group_ids": [CLAUDE_GROUP_ID]
                },
                headers={"Content-Type": "application/json"},
                timeout=GRAPHITI_TIMEOUT
            )
            
            return {
                "nodes": nodes_response.json() if nodes_response.status_code == 200 else [],
                "facts": facts_response.json() if facts_response.status_code == 200 else []
            }
            
        except Exception as e:
            logger.error(f"Error searching Graphiti: {e}")
            return {"nodes": [], "facts": []}

def main():
    """Main entry point for hook script"""
    try:
        # Read event data from stdin
        event_json = sys.stdin.read()
        event_data = json.loads(event_json)
        
        # Get event type
        event_type = event_data.get("event", "")
        
        # Initialize integration
        integration = GraphitiIntegration()
        
        # Process based on event type
        if event_type == "PostToolUse":
            integration.process_tool_event(event_data)
        elif event_type == "Notification":
            integration.process_notification(event_data)
            
    except Exception as e:
        logger.error(f"Hook error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()