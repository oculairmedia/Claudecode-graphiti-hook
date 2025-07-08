#!/usr/bin/env python3
"""
Session Analysis Module for Claude-Graphiti Integration
Analyzes full conversation transcripts to extract meaningful insights
"""

import json
import re
from typing import Dict, List, Optional, Set
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class SessionAnalyzer:
    """Analyzes Claude conversation sessions to extract insights"""
    
    def __init__(self):
        self.goal_keywords = [
            "help", "create", "build", "implement", "fix", "debug", "setup", 
            "install", "configure", "optimize", "refactor", "update", "add",
            "remove", "deploy", "test", "analyze", "understand", "explain"
        ]
        
        self.problem_indicators = [
            "error", "issue", "problem", "bug", "fail", "broken", "wrong",
            "not working", "doesn't work", "can't", "unable", "trouble"
        ]
        
        self.solution_indicators = [
            "fixed", "solved", "working", "success", "completed", "done",
            "resolved", "corrected", "updated", "implemented"
        ]
    
    def _extract_text_content(self, content) -> str:
        """Helper to extract text from various content formats"""
        if isinstance(content, str):
            return content
        elif isinstance(content, list):
            if content and isinstance(content[0], dict):
                # Handle Claude API format [{"type": "text", "text": "..."}]
                text_parts = [item.get('text', '') for item in content if item.get('type') == 'text']
                return ' '.join(text_parts)
            else:
                return ' '.join(str(item) for item in content)
        else:
            return str(content)
    
    def analyze_session(self, messages: List[Dict]) -> Dict:
        """Analyze a complete session and extract insights"""
        try:
            analysis = {
                "session_goal": self.extract_main_objective(messages),
                "files_modified": self.get_modified_files(messages),
                "problems_solved": self.identify_solutions(messages),
                "key_decisions": self.extract_decisions(messages),
                "technologies_used": self.identify_technologies(messages),
                "session_metrics": self.calculate_metrics(messages),
                "learning_outcomes": self.extract_learnings(messages),
                "follow_up_items": self.identify_follow_ups(messages)
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing session: {e}")
            return {"error": str(e)}
    
    def extract_main_objective(self, messages: List[Dict]) -> str:
        """Extract the main goal/objective of the session"""
        try:
            # Look at first few user messages for the main request
            user_messages = [m for m in messages[:10] if m.get('type') == 'user']
            
            if not user_messages:
                return "No clear objective identified"
                
            # Combine first few user messages
            early_requests = []
            for msg in user_messages[:3]:
                content = self._extract_text_content(msg.get('content', '')).strip()
                if content and len(content) > 10:  # Skip very short messages
                    early_requests.append(content)
            
            if not early_requests:
                return "No clear objective identified"
                
            # Find the most substantial request
            main_request = max(early_requests, key=len)
            
            # Extract key action verbs and objects
            words = main_request.lower().split()
            goals = []
            
            for i, word in enumerate(words):
                if word in self.goal_keywords:
                    # Get context around the goal keyword
                    context_start = max(0, i-2)
                    context_end = min(len(words), i+8)
                    context = ' '.join(words[context_start:context_end])
                    goals.append(context)
            
            if goals:
                return f"Primary goal: {goals[0]}"
            else:
                # Fallback: return first substantial user message (truncated)
                return f"Session focus: {main_request[:100]}..."
                
        except Exception as e:
            logger.error(f"Error extracting objective: {e}")
            return "Could not determine objective"
    
    def get_modified_files(self, messages: List[Dict]) -> List[Dict]:
        """Extract files that were modified during the session"""
        modified_files = {}
        
        try:
            tool_uses = [m for m in messages if m.get('type') == 'tool_use']
            
            for tool in tool_uses:
                tool_name = tool.get('tool', '')
                tool_input = tool.get('input', {})
                
                if tool_name in ['Write', 'Edit', 'MultiEdit']:
                    file_path = tool_input.get('file_path', '')
                    if file_path:
                        if file_path not in modified_files:
                            modified_files[file_path] = {
                                'file': file_path,
                                'operations': [],
                                'first_modified': tool.get('timestamp', ''),
                                'last_modified': tool.get('timestamp', '')
                            }
                        
                        modified_files[file_path]['operations'].append(tool_name)
                        modified_files[file_path]['last_modified'] = tool.get('timestamp', '')
            
            return list(modified_files.values())
            
        except Exception as e:
            logger.error(f"Error getting modified files: {e}")
            return []
    
    def identify_solutions(self, messages: List[Dict]) -> List[str]:
        """Identify problems that were solved during the session"""
        solutions = []
        
        try:
            # Look for problem-solution patterns
            user_messages = [m for m in messages if m.get('type') == 'user']
            assistant_messages = [m for m in messages if m.get('type') == 'assistant']
            
            # Find user messages mentioning problems
            problems = []
            for msg in user_messages:
                content = self._extract_text_content(msg.get('content', '')).lower()
                for indicator in self.problem_indicators:
                    if indicator in content:
                        problems.append({
                            'problem': self._extract_text_content(msg.get('content', ''))[:200],
                            'timestamp': msg.get('timestamp', '')
                        })
                        break
            
            # Find assistant messages indicating solutions
            for msg in assistant_messages:
                content = self._extract_text_content(msg.get('content', '')).lower()
                for indicator in self.solution_indicators:
                    if indicator in content:
                        solutions.append(f"Solution achieved: {self._extract_text_content(msg.get('content', ''))[:150]}...")
                        break
            
            # If no explicit solutions found, infer from successful tool usage
            if not solutions:
                successful_tools = [m for m in messages if m.get('type') == 'tool_result' and not m.get('error', False)]
                if successful_tools:
                    solutions.append(f"Successfully completed {len(successful_tools)} tool operations")
            
            return solutions[:5]  # Limit to top 5 solutions
            
        except Exception as e:
            logger.error(f"Error identifying solutions: {e}")
            return []
    
    def extract_decisions(self, messages: List[Dict]) -> List[str]:
        """Extract key technical decisions made during the session"""
        decisions = []
        
        try:
            decision_keywords = [
                "decided to", "chose to", "selected", "will use", "going with",
                "better to", "instead of", "approach", "strategy", "plan"
            ]
            
            assistant_messages = [m for m in messages if m.get('type') == 'assistant']
            
            for msg in assistant_messages:
                content = self._extract_text_content(msg.get('content', ''))
                for keyword in decision_keywords:
                    if keyword in content.lower():
                        # Extract sentence containing the decision
                        sentences = content.split('.')
                        for sentence in sentences:
                            if keyword in sentence.lower():
                                decision = sentence.strip()
                                if len(decision) > 20:  # Skip very short decisions
                                    decisions.append(decision[:200])
                                break
                        
                        if len(decisions) >= 5:  # Limit decisions
                            break
                            
                if len(decisions) >= 5:
                    break
            
            return decisions
            
        except Exception as e:
            logger.error(f"Error extracting decisions: {e}")
            return []
    
    def identify_technologies(self, messages: List[Dict]) -> List[str]:
        """Identify technologies, languages, and tools used"""
        technologies = set()
        
        try:
            # Common technologies to look for
            tech_patterns = {
                'languages': ['python', 'javascript', 'typescript', 'java', 'go', 'rust', 'c++', 'c#', 'php', 'ruby'],
                'frameworks': ['react', 'vue', 'angular', 'django', 'flask', 'express', 'fastapi', 'spring'],
                'tools': ['docker', 'kubernetes', 'git', 'npm', 'pip', 'yarn', 'webpack', 'babel'],
                'databases': ['postgres', 'mysql', 'mongodb', 'redis', 'elasticsearch', 'sqlite'],
                'platforms': ['aws', 'azure', 'gcp', 'heroku', 'vercel', 'netlify']
            }
            
            all_content = ' '.join([
                self._extract_text_content(m.get('content', '')) for m in messages 
                if m.get('type') in ['user', 'assistant']
            ]).lower()
            
            # Also check file extensions and tool usage
            tool_uses = [m for m in messages if m.get('type') == 'tool_use']
            for tool in tool_uses:
                tool_input = tool.get('input', {})
                if 'file_path' in tool_input:
                    file_path = tool_input['file_path'].lower()
                    if '.py' in file_path:
                        technologies.add('Python')
                    elif '.js' in file_path:
                        technologies.add('JavaScript')
                    elif '.ts' in file_path:
                        technologies.add('TypeScript')
                    elif '.java' in file_path:
                        technologies.add('Java')
                    elif '.go' in file_path:
                        technologies.add('Go')
            
            # Search for technology mentions
            for category, techs in tech_patterns.items():
                for tech in techs:
                    if tech in all_content:
                        technologies.add(tech.title())
            
            return sorted(list(technologies))
            
        except Exception as e:
            logger.error(f"Error identifying technologies: {e}")
            return []
    
    def calculate_metrics(self, messages: List[Dict]) -> Dict:
        """Calculate session metrics"""
        try:
            user_msgs = [m for m in messages if m.get('type') == 'user']
            assistant_msgs = [m for m in messages if m.get('type') == 'assistant']
            tool_uses = [m for m in messages if m.get('type') == 'tool_use']
            tool_results = [m for m in messages if m.get('type') == 'tool_result']
            
            successful_tools = [t for t in tool_results if not t.get('error', False)]
            failed_tools = [t for t in tool_results if t.get('error', False)]
            
            # Calculate session duration
            timestamps = [m.get('timestamp') for m in messages if m.get('timestamp')]
            duration = "Unknown"
            if len(timestamps) >= 2:
                try:
                    start = datetime.fromisoformat(timestamps[0].replace('Z', '+00:00'))
                    end = datetime.fromisoformat(timestamps[-1].replace('Z', '+00:00'))
                    duration_delta = end - start
                    duration = f"{duration_delta.total_seconds()/60:.1f} minutes"
                except:
                    pass
            
            return {
                'total_messages': len(messages),
                'user_messages': len(user_msgs),
                'assistant_messages': len(assistant_msgs),
                'tools_used': len(tool_uses),
                'successful_operations': len(successful_tools),
                'failed_operations': len(failed_tools),
                'success_rate': f"{(len(successful_tools) / max(len(tool_results), 1)) * 100:.1f}%" if tool_results else "N/A",
                'session_duration': duration
            }
            
        except Exception as e:
            logger.error(f"Error calculating metrics: {e}")
            return {}
    
    def extract_learnings(self, messages: List[Dict]) -> List[str]:
        """Extract key learnings from the session"""
        learnings = []
        
        try:
            learning_keywords = [
                "learned", "discovered", "found out", "realized", "understood",
                "turns out", "it appears", "the issue was", "the solution is"
            ]
            
            assistant_messages = [m for m in messages if m.get('type') == 'assistant']
            
            for msg in assistant_messages:
                content = self._extract_text_content(msg.get('content', ''))
                for keyword in learning_keywords:
                    if keyword in content.lower():
                        # Extract the learning
                        sentences = content.split('.')
                        for sentence in sentences:
                            if keyword in sentence.lower():
                                learning = sentence.strip()
                                if len(learning) > 15:
                                    learnings.append(learning[:200])
                                break
                        
                        if len(learnings) >= 3:
                            break
                            
                if len(learnings) >= 3:
                    break
            
            return learnings
            
        except Exception as e:
            logger.error(f"Error extracting learnings: {e}")
            return []
    
    def identify_follow_ups(self, messages: List[Dict]) -> List[str]:
        """Identify potential follow-up items or incomplete tasks"""
        follow_ups = []
        
        try:
            follow_up_keywords = [
                "next step", "should", "need to", "todo", "later", "follow up",
                "consider", "might want", "could also", "future", "next time"
            ]
            
            # Check last few assistant messages for follow-up items
            assistant_messages = [m for m in messages if m.get('type') == 'assistant']
            recent_messages = assistant_messages[-5:]  # Last 5 assistant messages
            
            for msg in recent_messages:
                content = self._extract_text_content(msg.get('content', ''))
                for keyword in follow_up_keywords:
                    if keyword in content.lower():
                        sentences = content.split('.')
                        for sentence in sentences:
                            if keyword in sentence.lower():
                                follow_up = sentence.strip()
                                if len(follow_up) > 15:
                                    follow_ups.append(follow_up[:200])
                                break
            
            # Check for failed operations that might need follow-up
            failed_tools = [m for m in messages if m.get('type') == 'tool_result' and m.get('error', False)]
            if failed_tools:
                follow_ups.append(f"Review {len(failed_tools)} failed operations")
            
            return follow_ups[:5]  # Limit to 5 follow-ups
            
        except Exception as e:
            logger.error(f"Error identifying follow-ups: {e}")
            return []