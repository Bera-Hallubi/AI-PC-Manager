"""
Logging configuration for AI PC Manager
Provides centralized logging setup with file and console output
"""

import os
import sys
from pathlib import Path
from loguru import logger
from config.settings import settings


def setup_logging():
    """Setup logging configuration"""
    
    # Remove default logger
    logger.remove()
    
    # Get logging configuration
    log_level = settings.get('logging.level', 'INFO')
    file_logging = settings.get('logging.file_logging', True)
    
    # Use user-writable directory for logs (fixes Program Files permission issue)
    if getattr(sys, 'frozen', False):
        # Running as PyInstaller executable
        import tempfile
        log_dir = Path(tempfile.gettempdir()) / "AI_PC_Manager" / "logs"
        log_file = str(log_dir / "ai_pc_manager.log")
    else:
        # Running as script
        log_file = settings.get('logging.log_file', './logs/ai_pc_manager.log')
    
    max_log_size = settings.get('logging.max_log_size', '10MB')
    backup_count = settings.get('logging.backup_count', 5)
    
    # Console logging (with PyInstaller compatibility)
    try:
        # Check if stdout is available and not None (PyInstaller compatibility)
        if hasattr(sys, 'stdout') and sys.stdout is not None:
            logger.add(
                sys.stdout,
                level=log_level,
                format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
                colorize=True
            )
        else:
            # Fallback for PyInstaller when stdout is None or doesn't exist
            logger.add(
                lambda msg: print(msg, end=''),
                level=log_level,
                format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
                colorize=False
            )
    except Exception as e:
        # Ultimate fallback - just use print without colors
        logger.add(
            lambda msg: print(msg.strip()),
            level=log_level,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            colorize=False
        )
    
    # File logging
    if file_logging:
        # Ensure logs directory exists
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Parse max log size
        size_mb = int(max_log_size.replace('MB', ''))
        max_bytes = size_mb * 1024 * 1024
        
        logger.add(
            log_file,
            level=log_level,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            rotation=max_bytes,
            retention=backup_count,
            compression="zip"
        )
    
    logger.info("Logging system initialized")


def get_logger(name: str = None):
    """Get a logger instance for a specific module"""
    if name:
        return logger.bind(name=name)
    return logger


# Initialize logging when module is imported
setup_logging()
