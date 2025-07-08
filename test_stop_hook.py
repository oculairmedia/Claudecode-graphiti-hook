#!/usr/bin/env python3
"""Test script for Stop hook session summary functionality"""

import json
import subprocess
import sys
import os
import glob
from datetime import datetime

def find_recent_transcript():
    """Find a recent transcript file for testing"""
    pattern = os.path.expanduser("~/.claude/projects/**/*.jsonl")
    files = glob.glob(pattern, recursive=True)
    if files:
        return max(files, key=os.path.getmtime)
    return None

def test_stop_hook():
    """Test the Stop hook with session summary"""
    hook_script = "/root/.claude/hooks/graphiti_integration.py"
    transcript = find_recent_transcript()
    
    if not transcript:
        print("No transcript files found for testing")
        return
        
    print(f"Testing Stop hook with transcript: {transcript}")
    
    # Create test Stop event
    stop_event = {
        "hook_event_name": "Stop",
        "session_id": "test-session-stop-123",
        "transcript_path": transcript,
        "timestamp": datetime.now().isoformat(),
        "stop_hook_active": False
    }
    
    print("\n" + "="*60)
    print("Testing Stop Hook - Session Summary")
    print("="*60)
    print(f"Session ID: {stop_event['session_id']}")
    print(f"Transcript: {os.path.basename(transcript)}")
    
    try:
        # Run the hook script
        process = subprocess.Popen(
            ["python3", hook_script],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        stdout, stderr = process.communicate(input=json.dumps(stop_event))
        
        print(f"\nHook execution:")
        if stderr:
            print(f"Output: {stderr}")
        
        if process.returncode == 0:
            print("✓ Stop hook executed successfully")
            print("✓ Session summary should be sent to Graphiti")
        else:
            print(f"✗ Stop hook failed with return code: {process.returncode}")
            
    except Exception as e:
        print(f"✗ Error testing Stop hook: {e}")

def test_session_analyzer():
    """Test the session analyzer independently"""
    print("\n" + "="*60)
    print("Testing Session Analyzer")
    print("="*60)
    
    try:
        # Import and test session analyzer
        sys.path.append('/root/.claude/hooks')
        from session_analyzer import SessionAnalyzer
        from graphiti_integration import TranscriptParser
        
        transcript = find_recent_transcript()
        if not transcript:
            print("No transcript for analyzer test")
            return
            
        # Parse transcript
        parser = TranscriptParser()
        messages = parser.parse_transcript(transcript)
        
        print(f"Parsed {len(messages)} messages from transcript")
        
        # Analyze session
        analyzer = SessionAnalyzer()
        analysis = analyzer.analyze_session(messages)
        
        print("\nSession Analysis Results:")
        print("-" * 40)
        
        if "session_goal" in analysis:
            print(f"Goal: {analysis['session_goal']}")
            
        if "files_modified" in analysis:
            files = analysis['files_modified']
            print(f"Files modified: {len(files)}")
            for file_info in files[:3]:
                print(f"  • {file_info.get('file', 'Unknown')}")
                
        if "technologies_used" in analysis:
            techs = analysis['technologies_used']
            if techs:
                print(f"Technologies: {', '.join(techs)}")
                
        if "session_metrics" in analysis:
            metrics = analysis['session_metrics']
            print(f"Duration: {metrics.get('session_duration', 'Unknown')}")
            print(f"Success rate: {metrics.get('success_rate', 'N/A')}")
            
        print("\n✓ Session analyzer working correctly")
        
    except Exception as e:
        print(f"✗ Session analyzer error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("Testing Stop Hook and Session Summary Functionality")
    print("=" * 60)
    
    # Test session analyzer first
    test_session_analyzer()
    
    # Then test the full Stop hook
    test_stop_hook()
    
    print("\n" + "="*60)
    print("Test complete!")
    print("Check Graphiti for the session summary entry.")
    print("="*60)