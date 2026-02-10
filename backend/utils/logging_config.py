"""
Logging configuration for the Diagnostic System.
Uses loguru for structured logging with file rotation.
"""
import sys
from pathlib import Path
from loguru import logger

# Create logs directory
LOGS_DIR = Path(__file__).parent.parent.parent / "logs"
LOGS_DIR.mkdir(exist_ok=True)

# Remove default handler
logger.remove()

# Console handler - INFO level
logger.add(
    sys.stderr,
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
    level="INFO",
    colorize=True
)

# Main log file - DEBUG level with rotation
logger.add(
    LOGS_DIR / "ddx_system.log",
    format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
    level="DEBUG",
    rotation="10 MB",
    retention="7 days",
    compression="zip"
)

# Error log file - ERROR level only
logger.add(
    LOGS_DIR / "errors.log",
    format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}\n{exception}",
    level="ERROR",
    rotation="5 MB",
    retention="30 days"
)

# Agent decisions log - for tracking LLM calls and diagnostic decisions
logger.add(
    LOGS_DIR / "agent_decisions.log",
    format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {message}",
    level="INFO",
    filter=lambda record: record["extra"].get("agent", False),
    rotation="50 MB",
    retention="14 days"
)

def get_logger(name: str):
    """Get a logger instance with the given name."""
    return logger.bind(name=name)

def get_agent_logger(agent_name: str):
    """Get a logger specifically for agent decision tracking."""
    return logger.bind(name=agent_name, agent=True)
