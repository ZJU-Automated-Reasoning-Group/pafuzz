"""
This file contains utility functions for program generation.
"""

import subprocess
import os
import signal
import shutil
import logging
from typing import Tuple, Optional, List, Union
from pathlib import Path
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

def check_undefined_behavior(cfilename: str, clang_path: Optional[str] = None,
                           csmith_runtime: Optional[str] = None) -> int:
    """
    Check whether the generated C program has undefined behavior.
    
    Args:
        cfilename: Path to the C source file
        clang_path: Path to clang compiler (uses config default if None)
        csmith_runtime: Path to csmith runtime (uses config default if None)
    
    Returns:
        0: No undefined behavior detected
        1: Runtime error detected
        2: Compilation error
        3: Execution timeout
    """
    clang = clang_path or config.CLANG
    runtime = csmith_runtime or config.CSMITH_HOME
    
    if not clang:
        logging.warning("Clang path not configured, skipping UB check")
        return 0
        
    exe = f"{cfilename}.exe-clang"
    out = f"{cfilename}.out-clang"

    # Compile with UBSan
    compile_cmd = [
        "timeout", "30s",
        clang, "-msse4.2", "-m64",
        f"-I{runtime}",
        "-O0", "-fsanitize=undefined",
        "-c", cfilename, "-o", exe
    ]

    try:
        ret_code, stdout, stderr = run_cmd(compile_cmd, config.SAN_COMPILE_TIMEOUT)
        if ret_code != 0:
            logging.error("Cannot compile program for UB check")
            return 2

        # Run the compiled program
        run_cmd_list = ["timeout", "30s", f"./{exe}"]
        with open(out, "w") as outf:
            result = subprocess.run(run_cmd_list,
                                    stdout=outf,
                                    stderr=subprocess.DEVNULL)
            if result.returncode != 0:
                logging.error("Program execution timeout during UB check")
                return 3

        # Check for runtime errors
        with open(out, "r") as outf:
            if any("runtime error" in line for line in outf):
                logging.error("Runtime error detected")
                return 1

        return 0

    finally:
        # Cleanup
        for file in [exe, out]:
            Path(file).unlink(missing_ok=True)
    
