"""
Logging configuration utility.
"""
import sys
import os
from pathlib import Path
from loguru import logger
from typing import Optional


class LoggerConfig:
    """Configures application logging with loguru."""
    
    def __init__(self, log_level: str = "INFO", log_file: Optional[str] = None):
        self.log_level = log_level.upper()
        self.log_file = log_file
        self._setup_logger()
    
    def _setup_logger(self):
        """Setup logger configuration."""
        # Remove default handler
        logger.remove()
        
        # Console handler with colored output
        logger.add(
            sys.stderr,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
            level=self.log_level,
            colorize=True
        )
        
        # File handler if specified
        if self.log_file:
            log_path = Path(self.log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            logger.add(
                self.log_file,
                format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
                level=self.log_level,
                rotation="10 MB",
                retention="1 week",
                compression="zip"
            )
    
    @staticmethod
    def setup_default_logging():
        """Setup default logging configuration."""
        log_level = os.getenv('LOG_LEVEL', 'INFO')
        log_dir = Path(__file__).parent.parent.parent / "logs"
        log_file = log_dir / "trading_system.log"
        
        LoggerConfig(log_level=log_level, log_file=str(log_file))
        
        logger.info("Logging system initialized")


# Initialize default logging when module is imported
LoggerConfig.setup_default_logging()