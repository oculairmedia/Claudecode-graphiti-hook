#!/usr/bin/env python3
"""Test script for Claude-Graphiti hook integration"""

import json
import subprocess
import sys
from datetime import datetime

# Test event data
test_events = [
    {
        "event": "PostToolUse",
        "tool": "Read",
        "timestamp": datetime.now().isoformat(),
        "parameters": {
            "file_path": "/test/example.py"
        }
    },
    {
        "event": "PostToolUse", 
        "tool": "Bash",
        "timestamp": datetime.now().isoformat(),
        "parameters": {
            "command": "ls -la"
        }
    },
    {
        "event": "Notification",
        "message": "Test notification from Claude",
        "timestamp": datetime.now().isoformat()
    }
]

def test_hook():
    """Test the hook with sample events"""
    hook_script = "/root/.claude/hooks/graphiti_integration.py"
    
    for i, event in enumerate(test_events):
        print(f"\nTesting event {i+1}: {event.get('event', 'Unknown')}")
        print(f"Event data: {json.dumps(event, indent=2)}")
        
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
                print(f"Hook output: {stderr}")
            
            if process.returncode == 0:
                print("✓ Hook executed successfully")
            else:
                print(f"✗ Hook failed with return code: {process.returncode}")
                
        except Exception as e:
            print(f"✗ Error testing hook: {e}")

if __name__ == "__main__":
    print("Testing Claude-Graphiti Hook Integration")
    print("=" * 40)
    test_hook()