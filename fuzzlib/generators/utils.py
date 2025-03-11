"""
This file contains utility functions for program generation.
"""

import subprocess
import os
import signal
import shutil
from . import config

def run_cmd(cmd, timeout, work_dir=None):
    if type(cmd) is not list:
        cmd = cmd.split(' ')
        cmd = list(filter(lambda x: x != '', cmd))
    
    if not work_dir:
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    else:
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=work_dir)
    
    try:
        output, error = process.communicate(timeout=timeout)
        output = output.decode('utf-8', errors='ignore')
        error = error.decode('utf-8', errors='ignore')
    except subprocess.TimeoutExpired:
        kill_all(process.pid)
        return 124, '', ''

    return process.returncode, output, error

def kill_all(pid):
    """
    Kill a process and all its children.
    
    Args:
        pid (int): Process ID to kill
    """
    try:
        parent = subprocess.Popen(f"ps -o pid --ppid {pid} --noheaders".split(),
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, _ = parent.communicate()
        
        # Kill children first
        for child_pid in stdout.decode().split():
            if child_pid.strip():
                kill_all(int(child_pid.strip()))
        
        # Kill the parent
        os.kill(pid, signal.SIGTERM)
    except:
        # Process might already be dead
        pass

def sanitize_check(src_file, include_path, tmp_dir):
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
    san_cmd = f"{config.CLANG} -fsanitize=address,undefined {include_path} {src_file} -o {tmp_dir}/san_check"
    res = run_cmd(san_cmd, config.SAN_COMPILE_TIMEOUT)
    
    if res[0] != 0:
        return -1  # Compilation failed
    
    # Run the compiled program with sanitizer
    exec_cmd = f"{tmp_dir}/san_check"
    res = run_cmd(exec_cmd, config.RUN_TIMEOUT)
    
    # Clean up
    if os.path.exists(f"{tmp_dir}/san_check"):
        os.remove(f"{tmp_dir}/san_check")
    
    # Return 0 if no sanitizer errors, -1 otherwise
    return 0 if res[0] == 0 else -1

def cleanup_tmp_files(tmp_dir, keep_source=False):
    """
    Clean up temporary files created during program generation and testing.
    
    Args:
        tmp_dir (str): Directory containing temporary files
        keep_source (bool): Whether to keep source files (.c, .h)
    
    Returns:
        bool: True if cleanup was successful, False otherwise
    """
    try:
        if not os.path.exists(tmp_dir):
            return True
            
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
    
