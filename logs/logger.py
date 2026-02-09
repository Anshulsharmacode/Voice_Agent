import logging
import sys
from typing import Optional
from pathlib import Path
import os
from enum import Enum
from datetime import datetime

# ANSI color codes
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    PURPLE = '\033[35m'
    ORANGE = '\033[33m'

class AgentLogType(Enum):
    BASE = "BASE"
    ASSISTANT = "ASSISTANT"
    TOOL = "TOOL"
    USER = "USER"
    SYSTEM = "SYSTEM"
    ERROR = "ERROR"
    WARNING = "WARNING"
    SUCCESS = "SUCCESS"
    INFO = "INFO"

class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors based on log type"""
    
    type_colors = {
        AgentLogType.BASE.value: Colors.BLUE,
        AgentLogType.ASSISTANT.value: Colors.GREEN,
        AgentLogType.TOOL.value: Colors.CYAN,
        AgentLogType.USER.value: Colors.PURPLE,
        AgentLogType.SYSTEM.value: Colors.YELLOW,
        AgentLogType.ERROR.value: Colors.RED,
        AgentLogType.WARNING.value: Colors.ORANGE,
        AgentLogType.SUCCESS.value: Colors.GREEN,
        AgentLogType.INFO.value: Colors.BLUE,
    }

    def format(self, record):
        # Extract log type from the record
        log_type = getattr(record, 'log_type', AgentLogType.BASE.value)
        color = self.type_colors.get(log_type, '')
        
        # Add color to the message
        record.msg = f"{color}{record.msg}{Colors.ENDC}"
        
        # Add log type to the message
        record.msg = f"[{log_type}] {record.msg}"
        
        return super().format(record)

class AgentLogger:
    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AgentLogger, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if AgentLogger._initialized:
            return
            
        AgentLogger._initialized = True
        
        # Create the logger
        self.logger = logging.getLogger('AgentLibrary')
        self.logger.setLevel(logging.INFO)
        
        # Clear any existing handlers
        self.logger.handlers = []
        
        # Create formatters
        console_formatter = ColoredFormatter(
            '%(asctime)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_formatter = logging.Formatter(
            '%(asctime)s - %(log_type)s [%(filename)s:%(lineno)d] - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)
        
        # File handler
        logs_dir = Path('logs')
        logs_dir.mkdir(exist_ok=True)
        file_handler = logging.FileHandler(logs_dir / 'agent.log')
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)

    def _log(self, level: int, message: str, log_type: AgentLogType):
        extra = {'log_type': log_type.value}
        self.logger.log(level, message, extra=extra)

    def base(self, message: str):
        """Basic log message"""
        self._log(logging.INFO, message, AgentLogType.BASE)

    def assistant(self, message: str):
        """Assistant-related log message"""
        self._log(logging.INFO, message, AgentLogType.ASSISTANT)

    def tool(self, message: str):
        """Tool-related log message"""
        self._log(logging.INFO, message, AgentLogType.TOOL)

    def user(self, message: str):
        """User-related log message"""
        self._log(logging.INFO, message, AgentLogType.USER)

    def system(self, message: str):
        """System-related log message"""
        self._log(logging.INFO, message, AgentLogType.SYSTEM)

    def error(self, message: str):
        """Error log message"""
        self._log(logging.ERROR, message, AgentLogType.ERROR)

    def warning(self, message: str):
        """Warning log message"""
        self._log(logging.WARNING, message, AgentLogType.WARNING)

    def success(self, message: str):
        """Success log message"""
        self._log(logging.INFO, message, AgentLogType.SUCCESS)
        
    def info(self, message: str):
        """Info log message"""
        self._log(logging.INFO, message, AgentLogType.INFO)

    def set_level(self, level: str):
        """Set the logging level"""
        level_map = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR,
            'CRITICAL': logging.CRITICAL
        }
        if level.upper() in level_map:
            self.logger.setLevel(level_map[level.upper()])

# Create a global logger instance
logger = AgentLogger()