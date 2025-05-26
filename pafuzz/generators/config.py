"""Configuration management for fuzzlib generators."""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# Default configuration
DEFAULT_CONFIG = {
    # Generators
    "YARPGEN": "yarpgen",
    "CSMITH": "csmith", 
    "CSMITH_HOME": "/home/csmith/runtime",
    
    # Timeouts (seconds)
    "YARPGEN_TIMEOUT": 10,
    "CSMITH_TIMEOUT": 15,
    "COMPILE_TIMEOUT": 30,
    "SAN_COMPILE_TIMEOUT": 30,
    "RUN_TIMEOUT": 15,
    "SHELL_TIMEOUT": 20,
    
    # Compilers
    "GCC": "gcc",
    "CLANG": "clang",
    
    # Sanitizer files
    "SAN_FILE": "",
    "YARP_SAN_FILE": "",
    
    # Constraints
    "MIN_PROGRAM_SIZE": 20000
}

class Config:
    """Configuration manager with validation and easy access."""
    
    def __init__(self, config_dict: Dict[str, Any]):
        self._config = config_dict.copy()
        self._validate()
    
    def _validate(self):
        """Validate configuration values."""
        for key, value in self._config.items():
            if key.endswith('_TIMEOUT') and not isinstance(value, (int, float)):
                raise ValueError(f"Timeout value {key} must be numeric")
            if key in ['MIN_PROGRAM_SIZE'] and not isinstance(value, int):
                raise ValueError(f"{key} must be an integer")
    
    def __getattr__(self, name: str) -> Any:
        if name in self._config:
            return self._config[name]
        raise AttributeError(f"Config has no attribute '{name}'")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get config value with optional default."""
        return self._config.get(key, default)
    
    def update(self, updates: Dict[str, Any]):
        """Update configuration with new values."""
        self._config.update(updates)
        self._validate()

def load_config(config_path: Optional[str] = None) -> Config:
    """Load configuration from file or use defaults."""
    config_dict = DEFAULT_CONFIG.copy()
    
    # Determine config path
    if not config_path:
        # First try environment variable
        config_path = os.environ.get('PAFUZZ_CONFIG')
        
        # If not set, try ../bintools/config.json relative to this file
        if not config_path:
            current_dir = Path(__file__).parent
            bintools_config = current_dir.parent.parent / 'config.json'
            if bintools_config.exists():
                config_path = bintools_config
            else:
                # Fall back to default location
                config_path = Path.home() / '.pafuzz' / 'config.json'
    
    # Load user config if exists
    if config_path and Path(config_path).exists():
        try:
            with open(config_path, 'r') as f:
                user_config = json.load(f)
                config_dict.update(user_config)
            logging.info(f"Configuration loaded from {config_path}")
        except Exception as e:
            logging.error(f"Error loading config from {config_path}: {e}")
    elif config_path:
        logging.warning(f"Config file {config_path} not found, using defaults")
    
    return Config(config_dict)

# Global config instance
config = load_config()

# Extract configuration values into module-level variables
YARPGEN = config.YARPGEN
CSMITH = config.CSMITH
CSMITH_HOME = config.CSMITH_HOME
SAN_FILE = config.SAN_FILE
YARP_SAN_FILE = config.YARP_SAN_FILE
GCC = config.GCC
CLANG = config.CLANG

YARPGEN_TIMEOUT = config.YARPGEN_TIMEOUT
CSMITH_TIMEOUT = config.CSMITH_TIMEOUT
SHELL_TIMEOUT = config.SHELL_TIMEOUT
COMPILE_TIMEOUT = config.COMPILE_TIMEOUT
SAN_COMPILE_TIMEOUT = config.SAN_COMPILE_TIMEOUT
RUN_TIMEOUT = config.RUN_TIMEOUT

MIN_PROGRAM_SIZE = config.MIN_PROGRAM_SIZE

