#!/usr/bin/env python3
"""Test script for enhanced Claude-Graphiti hook integration"""

import json
import subprocess
import sys
from datetime import datetime

# Find a real transcript for testing
import os
import glob

def find_recent_transcript():
    """Find a recent transcript file"""
    pattern = os.path.expanduser("~/.claude/projects/**/*.jsonl")
    files = glob.glob(pattern, recursive=True)
    if files:
        # Get most recent file
        return max(files, key=os.path.getmtime)
    return None

def test_enhanced_hook():
    """Test the enhanced hook with real transcript data"""
    hook_script = "/root/.claude/hooks/graphiti_integration_enhanced.py"
    transcript = find_recent_transcript()
    
    if not transcript:
        print("No transcript files found")
        return
        
    print(f"Using transcript: {transcript}")
    
    # Test events with transcript context
    test_events = [
        {
            "hook_event_name": "PostToolUse",
            "tool_name": "Read",
            "session_id": "test-session-123",
            "transcript_path": transcript,
            "timestamp": datetime.now().isoformat(),
            "tool_input": {
                "file_path": "/test/example.py"
            }
        },
        {
            "hook_event_name": "PostToolUse", 
            "tool_name": "Bash",
            "session_id": "test-session-123",
            "transcript_path": transcript,
            "timestamp": datetime.now().isoformat(),
            "tool_input": {
                "command": "ls -la",
                "description": "List directory contents"
            }
        },
        {
            "hook_event_name": "PostToolUse",
            "tool_name": "WebSearch",
            "session_id": "test-session-123", 
            "transcript_path": transcript,
            "timestamp": datetime.now().isoformat(),
            "tool_input": {
                "query": "python async programming best practices"
            }
        }
    ]
    
    for i, event in enumerate(test_events):
        print(f"\n{'='*60}")
        print(f"Testing event {i+1}: {event.get('tool_name', 'Unknown')}")
        
        try:
            # Run the hook script with the event data
            process = subprocess.Popen(
                ["python3", hook_script],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            stdout, stderr = process.communicate(input=json.dumps(event))
            
            if stderr:
                print(f"Hook output:\n{stderr}")
            
            if process.returncode == 0:
                print("✓ Hook executed successfully")
            else:
                print(f"✗ Hook failed with return code: {process.returncode}")
                
        except Exception as e:
            print(f"✗ Error testing hook: {e}")

if __name__ == "__main__":
    print("Testing Enhanced Claude-Graphiti Hook Integration")
    print("=" * 60)
    test_enhanced_hook()