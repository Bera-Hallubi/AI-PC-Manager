"""
AI Manager for AI PC Manager
Handles local LLM processing, command understanding, and response generation
"""

import os
import json
import re
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
import torch
from transformers import (
    AutoTokenizer, 
    AutoModelForCausalLM, 
    pipeline,
    set_seed
)
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings as ChromaSettings
import pandas as pd

from config.settings import settings
from utils.logger import get_logger

logger = get_logger(__name__)


class AIManager:
    """Core AI manager for local LLM processing and command understanding"""
    
    def __init__(self):
        self.config = settings.get_ai_config()
        self.memory_enabled = self.config.get('memory_enabled', True)
        self.model_cache_dir = self.config.get('model_cache_dir', './models')
        
        # Initialize models
        self.llm_model = None
        self.llm_tokenizer = None
        self.embedding_model = None
        self.memory_db = None
        
        # Command patterns for system control
        self.command_patterns = self._load_command_patterns()
        
        # Initialize AI components
        self._initialize_models()
        if self.memory_enabled:
            self._initialize_memory()
    
    def _initialize_models(self):
        """Initialize local LLM and embedding models"""
        try:
            # Create models directory
            os.makedirs(self.model_cache_dir, exist_ok=True)
            
            # Load primary model
            primary_model = self.config.get('primary_model', 'microsoft/DialoGPT-medium')
            logger.info(f"Loading primary model: {primary_model}")
            
            self.llm_tokenizer = AutoTokenizer.from_pretrained(
                primary_model,
                cache_dir=self.model_cache_dir
            )
            
            # Add padding token if not present
            if self.llm_tokenizer.pad_token is None:
                self.llm_tokenizer.pad_token = self.llm_tokenizer.eos_token
            
            self.llm_model = AutoModelForCausalLM.from_pretrained(
                primary_model,
                cache_dir=self.model_cache_dir,
                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                device_map="auto" if torch.cuda.is_available() else None
            )
            
            # Load embedding model for semantic search
            logger.info("Loading embedding model for semantic search")
            self.embedding_model = SentenceTransformer(
                'all-MiniLM-L6-v2',
                cache_folder=self.model_cache_dir
            )
            
            logger.info("AI models loaded successfully")
            
        except Exception as e:
            logger.error(f"Error loading AI models: {e}")
            # Fallback to a simpler model
            self._load_fallback_model()
    
    def _load_fallback_model(self):
        """Load a lightweight fallback model"""
        try:
            fallback_model = self.config.get('fallback_model', 'distilgpt2')
            logger.info(f"Loading fallback model: {fallback_model}")
            
            self.llm_tokenizer = AutoTokenizer.from_pretrained(fallback_model)
            if self.llm_tokenizer.pad_token is None:
                self.llm_tokenizer.pad_token = self.llm_tokenizer.eos_token
            
            self.llm_model = AutoModelForCausalLM.from_pretrained(fallback_model)
            
        except Exception as e:
            logger.error(f"Error loading fallback model: {e}")
            self.llm_model = None
            self.llm_tokenizer = None
    
    def _initialize_memory(self):
        """Initialize ChromaDB for conversation memory"""
        try:
            memory_path = os.path.join(self.model_cache_dir, 'memory')
            self.memory_db = chromadb.PersistentClient(
                path=memory_path,
                settings=ChromaSettings(anonymized_telemetry=False)
            )
            
            # Create or get collection
            self.memory_collection = self.memory_db.get_or_create_collection(
                name="conversation_memory",
                metadata={"description": "AI PC Manager conversation memory"}
            )
            
            logger.info("Memory system initialized")
            
        except Exception as e:
            logger.error(f"Error initializing memory: {e}")
            self.memory_enabled = False
    
    def _load_command_patterns(self) -> Dict[str, List[str]]:
        """Load command patterns for system control"""
        return {
            'greeting': [
                r'^(hi|hello|hey)\b',
                r'good\s+(morning|afternoon|evening)'
            ],
            'open_app': [
                r'open\s+(.+)',
                r'launch\s+(.+)',
                r'start\s+(.+)',
                r'run\s+(.+)'
            ],
            'close_app': [
                r'close\s+(.+)',
                r'quit\s+(.+)',
                r'exit\s+(.+)',
                r'stop\s+(.+)'
            ],
            'search': [
                r'search\s+for\s+(.+)',
                r'find\s+(.+)',
                r'where\s+is\s+(.+)',
                r'locate\s+(.+)'
            ],
            'screenshot': [
                r'take\s+a\s+screenshot',
                r'screenshot',
                r'capture\s+screen'
            ],
            'system_info': [
                r'system\s+info',
                r'pc\s+status',
                r'system\s+status',
                r'computer\s+info'
            ],
            'help': [
                r'help',
                r'what\s+can\s+you\s+do',
                r'commands',
                r'capabilities'
            ]
        }
    
    def process_command(self, command: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Process a user command and return AI response with action details
        
        Args:
            command: User command text
            context: Additional context information
            
        Returns:
            Dictionary containing response, action, and metadata
        """
        try:
            # Clean and normalize command
            command = command.strip().lower()
            
            # Check for direct command patterns first
            action_result = self._check_command_patterns(command)
            if action_result:
                return action_result
            
            # Use LLM for complex commands
            if self.llm_model and self.llm_tokenizer:
                llm_response = self._generate_llm_response(command, context)
                return self._parse_llm_response(llm_response, command)
            
            # Fallback to simple pattern matching
            return self._fallback_response(command)
            
        except Exception as e:
            logger.error(f"Error processing command: {e}")
            return {
                'response': f"I encountered an error processing your command: {str(e)}",
                'action': 'error',
                'confidence': 0.0,
                'metadata': {'error': str(e)}
            }
    
    def _check_command_patterns(self, command: str) -> Optional[Dict[str, Any]]:
        """Check if command matches known patterns"""
        for action_type, patterns in self.command_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, command, re.IGNORECASE)
                if match:
                    if action_type == 'greeting':
                        return {
                            'response': "Hello! How can I help you?",
                            'action': 'respond',
                            'target': None,
                            'confidence': 0.95,
                            'metadata': {'pattern_matched': pattern}
                        }
                    target = match.group(1).strip() if match.groups() else None
                    # If open/close without target, ask for clarification
                    if action_type in ('open_app', 'close_app') and (not target or len(target) < 2):
                        return {
                            'response': "Which application? Please say, for example, 'open calculator'.",
                            'action': 'respond',
                            'target': None,
                            'confidence': 0.7,
                            'metadata': {'pattern_matched': pattern}
                        }
                    return {
                        'response': f"I'll {action_type.replace('_', ' ')} for you.",
                        'action': action_type,
                        'target': target,
                        'confidence': 0.9,
                        'metadata': {'pattern_matched': pattern}
                    }
        return None
    
    def _generate_llm_response(self, command: str, context: Dict[str, Any] = None) -> str:
        """Generate response using local LLM"""
        try:
            # Prepare input
            prompt = self._create_prompt(command, context)
            
            # Tokenize input
            inputs = self.llm_tokenizer.encode(prompt, return_tensors='pt')
            
            # Generate response
            with torch.no_grad():
                outputs = self.llm_model.generate(
                    inputs,
                    max_length=self.config.get('max_length', 512),
                    temperature=self.config.get('temperature', 0.7),
                    top_p=self.config.get('top_p', 0.9),
                    do_sample=True,
                    pad_token_id=self.llm_tokenizer.eos_token_id,
                    eos_token_id=self.llm_tokenizer.eos_token_id
                )
            
            # Decode response
            response = self.llm_tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Extract only the new generated text
            response = response[len(prompt):].strip()
            
            return response
            
        except Exception as e:
            logger.error(f"Error generating LLM response: {e}")
            return "I'm having trouble processing that request right now."
    
    def _create_prompt(self, command: str, context: Dict[str, Any] = None) -> str:
        """Create a prompt for the LLM"""
        system_prompt = """You are an AI assistant that helps manage a PC. You can:
- Open and close applications
- Search for files and applications
- Take screenshots
- Provide system information
- Help with computer tasks

User command: """
        
        return f"{system_prompt}{command}\nAssistant:"
    
    def _parse_llm_response(self, response: str, original_command: str) -> Dict[str, Any]:
        """Parse LLM response and determine action"""
        response_lower = response.lower()
        
        # Determine action based on response content
        action = 'respond'
        target = None
        
        if any(word in response_lower for word in ['open', 'launch', 'start']):
            action = 'open_app'
            # Try to extract app name from response
            target = self._extract_app_name(response)
        elif any(word in response_lower for word in ['close', 'quit', 'exit']):
            action = 'close_app'
            target = self._extract_app_name(response)
        elif any(word in response_lower for word in ['search', 'find', 'locate']):
            action = 'search'
            target = self._extract_search_term(response)
        elif 'screenshot' in response_lower:
            action = 'screenshot'
        elif any(word in response_lower for word in ['system', 'status', 'info']):
            action = 'system_info'
        
        return {
            'response': response,
            'action': action,
            'target': target,
            'confidence': 0.7,
            'metadata': {'llm_generated': True}
        }
    
    def _extract_app_name(self, text: str) -> Optional[str]:
        """Extract application name from text"""
        # Simple extraction - look for quoted text or common app names
        import re
        
        # Look for quoted text
        quoted = re.search(r'"([^"]+)"', text)
        if quoted:
            return quoted.group(1)
        
        # Look for common app patterns
        app_patterns = [
            r'open\s+([a-zA-Z0-9\s]+)',
            r'launch\s+([a-zA-Z0-9\s]+)',
            r'start\s+([a-zA-Z0-9\s]+)'
        ]
        
        for pattern in app_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None
    
    def _extract_search_term(self, text: str) -> Optional[str]:
        """Extract search term from text"""
        import re
        
        search_patterns = [
            r'search\s+for\s+([a-zA-Z0-9\s]+)',
            r'find\s+([a-zA-Z0-9\s]+)',
            r'locate\s+([a-zA-Z0-9\s]+)'
        ]
        
        for pattern in search_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None
    
    def _fallback_response(self, command: str) -> Dict[str, Any]:
        """Fallback response when LLM is not available"""
        command_lower = command.lower()
        
        if any(word in command_lower for word in ['hello', 'hi', 'hey']):
            return {
                'response': "Hello! I'm your AI PC Manager. How can I help you today?",
                'action': 'respond',
                'confidence': 0.8
            }
        elif 'help' in command_lower:
            return {
                'response': "I can help you open applications, search for files, take screenshots, and manage your PC. What would you like me to do?",
                'action': 'help',
                'confidence': 0.9
            }
        else:
            return {
                'response': "I understand you want me to help with something, but I'm having trouble processing that specific request. Could you try rephrasing it?",
                'action': 'respond',
                'confidence': 0.5
            }
    
    def add_to_memory(self, command: str, response: str, action: str):
        """Add interaction to memory for learning"""
        if not self.memory_enabled or not self.memory_db:
            return
        
        try:
            # Create embedding for the command
            if self.embedding_model:
                embedding = self.embedding_model.encode(command).tolist()
            else:
                embedding = None
            
            # Store in memory
            self.memory_collection.add(
                documents=[command],
                embeddings=[embedding] if embedding else None,
                metadatas=[{
                    'response': response,
                    'action': action,
                    'timestamp': str(pd.Timestamp.now())
                }],
                ids=[f"cmd_{len(self.memory_collection.get()['ids'])}"]
            )
            
        except Exception as e:
            logger.error(f"Error adding to memory: {e}")
    
    def search_memory(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search conversation memory for similar interactions"""
        if not self.memory_enabled or not self.memory_db:
            return []
        
        try:
            if self.embedding_model:
                query_embedding = self.embedding_model.encode(query).tolist()
                results = self.memory_collection.query(
                    query_embeddings=[query_embedding],
                    n_results=limit
                )
            else:
                results = self.memory_collection.query(
                    query_texts=[query],
                    n_results=limit
                )
            
            return results['metadatas'][0] if results['metadatas'] else []
            
        except Exception as e:
            logger.error(f"Error searching memory: {e}")
            return []
    
    def get_help_text(self) -> str:
        """Get help text for available commands"""
        return """
🤖 AI PC Manager - Available Commands:

📱 Application Management:
• "Open [app name]" - Launch applications
• "Close [app name]" - Close applications
• "Search for [name]" - Find apps, files, or folders

📸 System Control:
• "Take a screenshot" - Capture screen
• "System info" - Get PC status
• "Help" - Show this help

💬 General:
• "Hello" - Greet the AI
• Ask questions about your computer
• Request help with tasks

The AI learns from your commands and gets better over time!
        """
    
    def cleanup(self):
        """Cleanup resources"""
        try:
            if self.llm_model:
                del self.llm_model
            if self.llm_tokenizer:
                del self.llm_tokenizer
            if self.embedding_model:
                del self.embedding_model
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            
            logger.info("AI Manager cleaned up successfully")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")


# Global AI manager instance
ai_manager = AIManager()
