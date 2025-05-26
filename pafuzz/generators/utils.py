"""
This file contains utility functions for program generation.
"""

import subprocess
import os
import signal
import shutil
from typing import Tuple, Optional, List, Union
from pafuzz.generators.config import config

def run_cmd(cmd: Union[str, List[str]], timeout: int, 
           work_dir: Optional[str] = None) -> Tuple[int, str, str]:
    """Run a command with timeout and return (returncode, stdout, stderr)."""
    if isinstance(cmd, str):
        cmd = [x for x in cmd.split() if x]
    
    try:
        process = subprocess.Popen(
            cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            cwd=work_dir
        )
        stdout, stderr = process.communicate(timeout=timeout)
        return (
            process.returncode,
            stdout.decode('utf-8', errors='ignore'),
            stderr.decode('utf-8', errors='ignore')
        )
    except subprocess.TimeoutExpired:
        _kill_process_tree(process.pid)
        return 124, '', 'Command timed out'
    except Exception as e:
        return -1, '', f'Command failed: {e}'

def _kill_process_tree(pid: int):
    """Kill a process and all its children."""
    try:
        # Get child processes
        result = subprocess.run(
            ['ps', '-o', 'pid', '--ppid', str(pid), '--noheaders'],
            capture_output=True, text=True
        )
        
        # Kill children recursively
        for child_pid in result.stdout.split():
            if child_pid.strip():
                _kill_process_tree(int(child_pid.strip()))
        
        # Kill parent
        os.kill(pid, signal.SIGTERM)
    except (ProcessLookupError, ValueError):
        pass  # Process already dead or invalid PID

def sanitize_check(src_file: str, include_path: str, tmp_dir: str) -> int:
    """
    Check if a generated program passes sanitizer checks.
    
    Args:
        src_file (str): Path to the source file
        include_path (str): Include path for compilation
        tmp_dir (str): Directory for temporary files
    
    Returns:
        int: 0 if check passes, -1 if it fails
    """
    if not config.SAN_FILE:
        return 0  # Skip check if no sanitizer file is configured
    
    # Compile with sanitizer options
    san_cmd = [
        config.CLANG, 
        '-fsanitize=address,undefined',
        include_path,
        src_file,
        '-o', f'{tmp_dir}/san_check'
    ]
    
    ret_code, _, _ = run_cmd(san_cmd, config.SAN_COMPILE_TIMEOUT)
    if ret_code != 0:
        return -1  # Compilation failed
    
    # Run the compiled program with sanitizer
    ret_code, _, _ = run_cmd(f'{tmp_dir}/san_check', config.RUN_TIMEOUT)
    
    # Clean up
    _safe_remove(f'{tmp_dir}/san_check')
    
    # Return 0 if no sanitizer errors, -1 otherwise
    return 0 if ret_code == 0 else -1

def cleanup_tmp_files(tmp_dir: str, keep_source: bool = False) -> bool:
    """
    Clean up temporary files created during program generation and testing.
    
    Args:
        tmp_dir (str): Directory containing temporary files
        keep_source (bool): Whether to keep source files (.c, .h)
    
    Returns:
        bool: True if cleanup was successful, False otherwise
    """
    if not os.path.exists(tmp_dir):
        return True
            
    try:
        for filename in os.listdir(tmp_dir):
            filepath = os.path.join(tmp_dir, filename)
            
            # Skip source files if keep_source is True
            if keep_source and (filename.endswith('.c') or filename.endswith('.h')):
                continue
                
            # Remove executable files and other temporary files
            if os.path.isfile(filepath):
                os.remove(filepath)
            elif os.path.isdir(filepath):
                shutil.rmtree(filepath)
                
        return True
    except Exception as e:
        print(f"Error during cleanup: {e}", flush=True)
        return False

def _safe_remove(filepath: str):
    """Safely remove a file, ignoring errors."""
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
    except OSError:
        pass
    
