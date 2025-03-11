import os
import json
import logging
from pathlib import Path

# Default configuration values
DEFAULT_CONFIG = {
    # Program generators
    "YARPGEN": "yarpgen",
    "CSMITH": "csmith",
    "CSMITH_HOME": "/home/csmith/runtime",

    "YARPGEN_TIMEOUT": 10,
    "CSMITH_TIMEOUT": 15,

    # Compilers
    "GCC": "gcc",
    "CLANG": "clang",
    
    "COMPILE_TIMEOUT": 30,
    "SAN_COMPILE_TIMEOUT": 30,
    
    "RUN_TIMEOUT": 15,
    
    # Sanitizer files
    "SAN_FILE": "",
    "YARP_SAN_FILE": "",
    
    # Shell timeout
    "SHELL_TIMEOUT": 20,
    
    # Other constants
    "MIN_PROGRAM_SIZE": 20000
}

def load_config(config_path=None):
    """Load configuration from a JSON file, falling back to defaults if needed."""
    config = DEFAULT_CONFIG.copy()
    
    if config_path and os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                user_config = json.load(f)
                config.update(user_config)
            logging.info(f"Configuration loaded from {config_path}")
        except Exception as e:
            logging.error(f"Error loading configuration from {config_path}: {e}")
            logging.info("Using default configuration")
    else:
        if config_path:
            logging.warning(f"Configuration file {config_path} not found. Using default configuration.")
        else:
            logging.info("No configuration file specified. Using default configuration.")
    
    return config

# Load configuration from environment variable or use default path
config_path = os.environ.get('FUZZIT_CONFIG', os.path.join(str(Path.home()), '.fuzzit', 'config.json'))
config = load_config(config_path)

# Extract configuration values into module-level variables
YARPGEN = config["YARPGEN"]
CSMITH = config["CSMITH"]
CSMITH_HOME = config["CSMITH_HOME"]
SAN_FILE = config["SAN_FILE"]
YARP_SAN_FILE = config["YARP_SAN_FILE"]
GCC = config["GCC"]
CLANG = config["CLANG"]

YARPGEN_TIMEOUT = config["YARPGEN_TIMEOUT"]
CSMITH_TIMEOUT = config["CSMITH_TIMEOUT"]
SHELL_TIMEOUT = config["SHELL_TIMEOUT"]
COMPILE_TIMEOUT = config["COMPILE_TIMEOUT"]
SAN_COMPILE_TIMEOUT = config["SAN_COMPILE_TIMEOUT"]
RUN_TIMEOUT = config["RUN_TIMEOUT"]

MIN_PROGRAM_SIZE = config["MIN_PROGRAM_SIZE"]

