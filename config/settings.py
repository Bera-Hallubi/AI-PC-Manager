"""
Settings management for AI PC Manager
Handles configuration loading and validation
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from loguru import logger


class Settings:
    """Centralized settings management for the application"""
    
    def __init__(self, config_path: str = "config/config.yaml"):
        self.config_path = config_path
        self.config: Dict[str, Any] = {}
        self.load_config()
    
    def load_config(self) -> None:
        """Load configuration from YAML file"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as file:
                    self.config = yaml.safe_load(file) or {}
                logger.info(f"Configuration loaded from {self.config_path}")
            else:
                logger.warning(f"Config file not found: {self.config_path}, using defaults")
                self._create_default_config()
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            self._create_default_config()
    
    def _create_default_config(self) -> None:
        """Create default configuration if file doesn't exist"""
        self.config = {
            "app": {
                "name": "AI PC Manager",
                "version": "1.0.0",
                "debug": False,
                "theme": "dark"
            },
            "ai": {
                "primary_model": "microsoft/DialoGPT-medium",
                "fallback_model": "distilgpt2",
                "max_length": 512,
                "temperature": 0.7,
                "memory_enabled": True
            },
            "stt": {
                "engine": "whisper",
                "whisper_model": "base",
                "device": "cpu",
                "language": "en"
            },
            "tts": {
                "engine": "pyttsx3",
                "voice_rate": 200,
                "voice_volume": 0.8
            },
            "system": {
                "auto_discover_apps": True,
                "search_depth": 10,
                "search_timeout": 30
            },
            "ui": {
                "window_width": 1200,
                "window_height": 800,
                "theme": "dark"
            },
            "logging": {
                "level": "INFO",
                "file_logging": True
            }
        }
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation
        Example: settings.get('ai.primary_model')
        """
        keys = key_path.split('.')
        value = self.config
        
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key_path: str, value: Any) -> None:
        """
        Set configuration value using dot notation
        Example: settings.set('ai.temperature', 0.8)
        """
        keys = key_path.split('.')
        config = self.config
        
        # Navigate to the parent of the target key
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        
        # Set the value
        config[keys[-1]] = value
    
    def save_config(self) -> bool:
        """Save current configuration to file"""
        try:
            # Ensure config directory exists
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            
            with open(self.config_path, 'w', encoding='utf-8') as file:
                yaml.dump(self.config, file, default_flow_style=False, indent=2)
            
            logger.info(f"Configuration saved to {self.config_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving config: {e}")
            return False
    
    def get_ai_config(self) -> Dict[str, Any]:
        """Get AI-specific configuration"""
        return self.get('ai', {})
    
    def get_stt_config(self) -> Dict[str, Any]:
        """Get Speech-to-Text configuration"""
        return self.get('stt', {})
    
    def get_tts_config(self) -> Dict[str, Any]:
        """Get Text-to-Speech configuration"""
        return self.get('tts', {})
    
    def get_system_config(self) -> Dict[str, Any]:
        """Get system control configuration"""
        return self.get('system', {})
    
    def get_ui_config(self) -> Dict[str, Any]:
        """Get UI configuration"""
        return self.get('ui', {})
    
    def is_debug_mode(self) -> bool:
        """Check if debug mode is enabled"""
        return self.get('app.debug', False)
    
    def get_theme(self) -> str:
        """Get current theme setting"""
        return self.get('app.theme', 'dark')
    
    def set_theme(self, theme: str) -> None:
        """Set theme and save configuration"""
        self.set('app.theme', theme)
        self.save_config()


# Global settings instance
settings = Settings()
