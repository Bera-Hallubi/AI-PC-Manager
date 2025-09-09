"""
Command Learning System for AI PC Manager
Learns from user commands and improves recognition over time
"""

import os
import json
import time
import re
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import difflib

from config.settings import settings
from utils.logger import get_logger

logger = get_logger(__name__)


class CommandLearner:
    """Learns from user commands and improves pattern recognition"""
    
    def __init__(self):
        self.data_path = settings.get('data.base_path', './data')
        self.command_history_file = os.path.join(self.data_path, 'command_history.json')
        self.learned_patterns_file = os.path.join(self.data_path, 'learned_patterns.json')
        
        # Learning data
        self.command_history = []
        self.learned_patterns = {}
        self.command_frequency = Counter()
        self.success_rates = defaultdict(list)
        self.user_preferences = {}
        
        # Learning parameters
        self.min_pattern_frequency = 3  # Minimum occurrences to create pattern
        self.similarity_threshold = 0.7  # Minimum similarity for pattern matching
        self.max_pattern_length = 50  # Maximum words in a pattern
        self.learning_enabled = True
        
        # Load existing data
        self._load_data()
    
    def _load_data(self):
        """Load existing learning data from files"""
        try:
            # Load command history
            if os.path.exists(self.command_history_file):
                with open(self.command_history_file, 'r', encoding='utf-8') as f:
                    self.command_history = json.load(f)
                logger.info(f"Loaded {len(self.command_history)} commands from history")
            
            # Load learned patterns
            if os.path.exists(self.learned_patterns_file):
                with open(self.learned_patterns_file, 'r', encoding='utf-8') as f:
                    self.learned_patterns = json.load(f)
                logger.info(f"Loaded {len(self.learned_patterns)} learned patterns")
            
            # Rebuild frequency counters
            for command_data in self.command_history:
                command = command_data.get('command', '').lower()
                self.command_frequency[command] += 1
                
                # Rebuild success rates
                action = command_data.get('action', '')
                success = command_data.get('success', False)
                self.success_rates[action].append(success)
            
        except Exception as e:
            logger.error(f"Error loading learning data: {e}")
            self.command_history = []
            self.learned_patterns = {}
    
    def _save_data(self):
        """Save learning data to files"""
        try:
            os.makedirs(self.data_path, exist_ok=True)
            
            # Save command history
            with open(self.command_history_file, 'w', encoding='utf-8') as f:
                json.dump(self.command_history, f, indent=2, default=str)
            
            # Save learned patterns
            with open(self.learned_patterns_file, 'w', encoding='utf-8') as f:
                json.dump(self.learned_patterns, f, indent=2, default=str)
            
            logger.debug("Learning data saved successfully")
            
        except Exception as e:
            logger.error(f"Error saving learning data: {e}")
    
    def learn_from_command(self, command: str, action: str, success: bool, 
                          response: str = None, metadata: Dict[str, Any] = None):
        """
        Learn from a user command
        
        Args:
            command: The user command
            action: The action taken
            success: Whether the action was successful
            response: AI response to the command
            metadata: Additional metadata
        """
        if not self.learning_enabled:
            return
        
        try:
            # Create command record
            command_record = {
                'command': command,
                'action': action,
                'success': success,
                'response': response,
                'timestamp': time.time(),
                'datetime': datetime.now().isoformat(),
                'metadata': metadata or {}
            }
            
            # Add to history
            self.command_history.append(command_record)
            
            # Update frequency counter
            command_lower = command.lower()
            self.command_frequency[command_lower] += 1
            
            # Update success rates
            self.success_rates[action].append(success)
            
            # Learn patterns if command was successful
            if success:
                self._extract_patterns(command, action)
            
            # Update user preferences
            self._update_preferences(command, action, success)
            
            # Keep only recent history (last 1000 commands)
            if len(self.command_history) > 1000:
                self.command_history = self.command_history[-1000:]
            
            # Save data periodically
            if len(self.command_history) % 10 == 0:
                self._save_data()
            
            logger.debug(f"Learned from command: {command} -> {action} ({'success' if success else 'failed'})")
            
        except Exception as e:
            logger.error(f"Error learning from command: {e}")
    
    def _extract_patterns(self, command: str, action: str):
        """Extract patterns from successful commands"""
        try:
            command_lower = command.lower().strip()
            words = command_lower.split()
            
            # Skip very short or very long commands
            if len(words) < 2 or len(words) > self.max_pattern_length:
                return
            
            # Create n-gram patterns
            for n in range(2, min(len(words) + 1, 6)):  # 2-gram to 5-gram
                for i in range(len(words) - n + 1):
                    pattern = ' '.join(words[i:i+n])
                    
                    if pattern not in self.learned_patterns:
                        self.learned_patterns[pattern] = {
                            'action': action,
                            'frequency': 0,
                            'success_rate': 0.0,
                            'examples': [],
                            'created_at': time.time()
                        }
                    
                    # Update pattern data
                    pattern_data = self.learned_patterns[pattern]
                    pattern_data['frequency'] += 1
                    pattern_data['examples'].append(command)
                    
                    # Keep only recent examples (last 10)
                    if len(pattern_data['examples']) > 10:
                        pattern_data['examples'] = pattern_data['examples'][-10:]
                    
                    # Calculate success rate for this pattern
                    pattern_successes = sum(1 for cmd in self.command_history 
                                         if pattern in cmd.get('command', '').lower() 
                                         and cmd.get('success', False))
                    pattern_total = sum(1 for cmd in self.command_history 
                                     if pattern in cmd.get('command', '').lower())
                    
                    if pattern_total > 0:
                        pattern_data['success_rate'] = pattern_successes / pattern_total
            
        except Exception as e:
            logger.error(f"Error extracting patterns: {e}")
    
    def _update_preferences(self, command: str, action: str, success: bool):
        """Update user preferences based on command patterns"""
        try:
            command_lower = command.lower()
            
            # Track preferred applications
            if action == 'open_app' and success:
                app_name = self._extract_app_name(command)
                if app_name:
                    if 'preferred_apps' not in self.user_preferences:
                        self.user_preferences['preferred_apps'] = Counter()
                    self.user_preferences['preferred_apps'][app_name] += 1
            
            # Track command preferences
            if 'command_preferences' not in self.user_preferences:
                self.user_preferences['command_preferences'] = Counter()
            self.user_preferences['command_preferences'][command_lower] += 1
            
            # Track action preferences
            if 'action_preferences' not in self.user_preferences:
                self.user_preferences['action_preferences'] = Counter()
            self.user_preferences['action_preferences'][action] += 1
            
        except Exception as e:
            logger.error(f"Error updating preferences: {e}")
    
    def _extract_app_name(self, command: str) -> Optional[str]:
        """Extract application name from command"""
        try:
            # Common patterns for app names
            patterns = [
                r'open\s+(.+)',
                r'launch\s+(.+)',
                r'start\s+(.+)',
                r'run\s+(.+)'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, command, re.IGNORECASE)
                if match:
                    return match.group(1).strip()
            
            return None
            
        except Exception as e:
            logger.error(f"Error extracting app name: {e}")
            return None
    
    def suggest_command(self, partial_command: str) -> List[Dict[str, Any]]:
        """
        Suggest commands based on partial input
        
        Args:
            partial_command: Partial command text
            
        Returns:
            List of suggested commands with confidence scores
        """
        try:
            if not partial_command.strip():
                return self._get_popular_commands()
            
            partial_lower = partial_command.lower().strip()
            suggestions = []
            
            # Find exact matches in learned patterns
            for pattern, data in self.learned_patterns.items():
                if partial_lower in pattern:
                    confidence = self._calculate_confidence(pattern, data)
                    suggestions.append({
                        'command': pattern,
                        'action': data['action'],
                        'confidence': confidence,
                        'type': 'pattern_match',
                        'frequency': data['frequency'],
                        'success_rate': data['success_rate']
                    })
            
            # Find similar commands from history
            for command_data in self.command_history:
                command = command_data.get('command', '').lower()
                if command and command != partial_lower:
                    similarity = difflib.SequenceMatcher(None, partial_lower, command).ratio()
                    if similarity >= self.similarity_threshold:
                        suggestions.append({
                            'command': command_data['command'],
                            'action': command_data['action'],
                            'confidence': similarity,
                            'type': 'similarity_match',
                            'success': command_data.get('success', False)
                        })
            
            # Sort by confidence and frequency
            suggestions.sort(key=lambda x: (x['confidence'], x.get('frequency', 0)), reverse=True)
            
            return suggestions[:10]  # Return top 10 suggestions
            
        except Exception as e:
            logger.error(f"Error suggesting commands: {e}")
            return []
    
    def _get_popular_commands(self) -> List[Dict[str, Any]]:
        """Get most popular commands"""
        try:
            popular = []
            
            # Get most frequent commands
            for command, frequency in self.command_frequency.most_common(10):
                if frequency > 1:  # Only include commands used more than once
                    # Find the most recent successful execution
                    recent_success = any(
                        cmd.get('command', '').lower() == command and cmd.get('success', False)
                        for cmd in self.command_history[-50:]  # Check last 50 commands
                    )
                    
                    popular.append({
                        'command': command,
                        'frequency': frequency,
                        'confidence': min(frequency / 10.0, 1.0),  # Normalize confidence
                        'type': 'popular',
                        'recent_success': recent_success
                    })
            
            return popular
            
        except Exception as e:
            logger.error(f"Error getting popular commands: {e}")
            return []
    
    def _calculate_confidence(self, pattern: str, data: Dict[str, Any]) -> float:
        """Calculate confidence score for a pattern"""
        try:
            frequency = data.get('frequency', 0)
            success_rate = data.get('success_rate', 0.0)
            
            # Base confidence from frequency and success rate
            confidence = (frequency * 0.3) + (success_rate * 0.7)
            
            # Normalize to 0-1 range
            confidence = min(confidence, 1.0)
            
            return confidence
            
        except Exception as e:
            logger.error(f"Error calculating confidence: {e}")
            return 0.0
    
    def get_command_statistics(self) -> Dict[str, Any]:
        """Get statistics about learned commands"""
        try:
            total_commands = len(self.command_history)
            successful_commands = sum(1 for cmd in self.command_history if cmd.get('success', False))
            success_rate = (successful_commands / total_commands * 100) if total_commands > 0 else 0
            
            # Action statistics
            action_stats = {}
            for action, successes in self.success_rates.items():
                total = len(successes)
                successful = sum(successes)
                action_stats[action] = {
                    'total': total,
                    'successful': successful,
                    'success_rate': (successful / total * 100) if total > 0 else 0
                }
            
            # Most used commands (ensure it's a list of tuples)
            most_used = list(self.command_frequency.most_common(10))
            
            # Most learned patterns
            most_patterns = sorted(
                self.learned_patterns.items(),
                key=lambda x: x[1]['frequency'],
                reverse=True
            )[:10]
            
            return {
                'total_commands': total_commands,
                'successful_commands': successful_commands,
                'overall_success_rate': round(success_rate, 2),
                'action_statistics': action_stats,
                'most_used_commands': most_used,
                'most_learned_patterns': most_patterns,
                'total_patterns': len(self.learned_patterns),
                'learning_enabled': self.learning_enabled
            }
            
        except Exception as e:
            logger.error(f"Error getting command statistics: {e}")
            return {}
    
    def get_user_preferences(self) -> Dict[str, Any]:
        """Get learned user preferences"""
        try:
            # Convert Counter objects to regular dictionaries
            preferences = {}
            
            if 'preferred_apps' in self.user_preferences:
                preferences['preferred_apps'] = list(self.user_preferences['preferred_apps'].most_common(10))
            
            if 'command_preferences' in self.user_preferences:
                preferences['command_preferences'] = dict(self.user_preferences['command_preferences'].most_common(10))
            
            if 'action_preferences' in self.user_preferences:
                preferences['action_preferences'] = dict(self.user_preferences['action_preferences'].most_common(10))
            
            return preferences
            
        except Exception as e:
            logger.error(f"Error getting user preferences: {e}")
            return {}
    
    def improve_pattern(self, pattern: str, feedback: str) -> bool:
        """
        Improve a pattern based on user feedback
        
        Args:
            pattern: The pattern to improve
            feedback: User feedback ('good', 'bad', 'better_alternative')
            
        Returns:
            True if pattern was updated successfully
        """
        try:
            if pattern not in self.learned_patterns:
                return False
            
            pattern_data = self.learned_patterns[pattern]
            
            if feedback == 'good':
                # Increase success rate
                pattern_data['success_rate'] = min(pattern_data['success_rate'] + 0.1, 1.0)
            elif feedback == 'bad':
                # Decrease success rate
                pattern_data['success_rate'] = max(pattern_data['success_rate'] - 0.1, 0.0)
            
            # Update last modified time
            pattern_data['last_modified'] = time.time()
            
            self._save_data()
            logger.info(f"Improved pattern '{pattern}' based on feedback: {feedback}")
            return True
            
        except Exception as e:
            logger.error(f"Error improving pattern: {e}")
            return False
    
    def clear_learning_data(self, keep_recent: bool = True) -> bool:
        """
        Clear learning data
        
        Args:
            keep_recent: Whether to keep recent commands (last 100)
            
        Returns:
            True if data was cleared successfully
        """
        try:
            if keep_recent:
                # Keep only last 100 commands
                self.command_history = self.command_history[-100:]
            else:
                self.command_history = []
            
            # Clear patterns but keep structure
            self.learned_patterns = {}
            
            # Reset counters
            self.command_frequency.clear()
            self.success_rates.clear()
            self.user_preferences.clear()
            
            # Save cleared data
            self._save_data()
            
            logger.info("Learning data cleared successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error clearing learning data: {e}")
            return False
    
    def export_learning_data(self, filepath: str) -> bool:
        """Export learning data to file"""
        try:
            export_data = {
                'command_history': self.command_history,
                'learned_patterns': self.learned_patterns,
                'command_frequency': dict(self.command_frequency),
                'success_rates': {k: list(v) for k, v in self.success_rates.items()},
                'user_preferences': {k: dict(v) if isinstance(v, Counter) else v 
                                   for k, v in self.user_preferences.items()},
                'export_timestamp': time.time(),
                'export_datetime': datetime.now().isoformat()
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, default=str)
            
            logger.info(f"Learning data exported to {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting learning data: {e}")
            return False
    
    def cleanup(self):
        """Cleanup resources and save data"""
        try:
            self._save_data()
            logger.info("Command learner cleaned up successfully")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")


# Global command learner instance
command_learner = CommandLearner()
