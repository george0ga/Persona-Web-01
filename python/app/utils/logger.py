from loguru import logger
import os
import sys

log_dir = os.path.join(os.path.dirname(__file__), "..", "..", "logs")
os.makedirs(log_dir, exist_ok=True)

logger.remove()

logger.add(sys.stdout, level="INFO", colorize=True, backtrace=True, diagnose=True)

logger.add(
    os.path.join(log_dir, "parser.log"),
    level="DEBUG",
    encoding="utf-8",
    rotation="5 MB",        
    retention="10 days",    
    compression="zip",      
)

