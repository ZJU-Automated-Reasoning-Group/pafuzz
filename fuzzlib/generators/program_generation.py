import random
import os
from .config import (CSMITH, CSMITH_HOME, CSMITH_TIMEOUT, MIN_PROGRAM_SIZE,
                    YARPGEN, YARPGEN_TIMEOUT, YARP_SAN_FILE)
from .utils import run_cmd, sanitize_check


def gen_program(seed, tmp_dir):
    """
    Generate a C program using Csmith with minimal options.
    
    Args:
        seed (int): Random seed for generation
        tmp_dir (str): Directory to store the generated program
    
    Returns:
        str: Path to the generated source file, or -1 if generation failed
    """
    # Simple command with just the essential options
    gen_command = f'{CSMITH} --concise --seed {seed} -o {tmp_dir}/{seed}.c'
    
    res = run_cmd(gen_command, CSMITH_TIMEOUT)
    if res[0] != 0:
        return -1

    src_file = f'{tmp_dir}/{seed}.c'
    if os.path.getsize(src_file) < MIN_PROGRAM_SIZE:
        print(f'{src_file} failed, program size', flush=True)
        return -1

    san_ret = sanitize_check(src_file, f'-I{CSMITH_HOME}', tmp_dir)
    if san_ret == -1:
        print(f'{src_file} failed, sanitization', flush=True)
        return -1

    return src_file

def generate_program_yarpgen(tmp_dir, seed=None):
    """
    Generate a C program using YARPGen with minimal options.
    
    Args:
        tmp_dir (str): Directory to store the generated program
        seed (int, optional): Random seed for generation. If None, a random seed will be used.
    
    Returns:
        str: Path to the generated source file, or -1 if generation failed
    """
    if seed is None:
        seed = random.randint(0, 9999999999)
    
    # Ensure tmp_dir exists
    os.makedirs(tmp_dir, exist_ok=True)
    
    # Simplified YARPGen command
    gen_command = f'{YARPGEN} --std=c --seed {seed} --out-dir {tmp_dir}'
    
    res = run_cmd(gen_command, YARPGEN_TIMEOUT)
    if res[0] != 0:
        return -1
    
    src_file = f'{tmp_dir}/driver.c'
    
    if not os.path.exists(src_file) or os.path.getsize(src_file) < MIN_PROGRAM_SIZE:
        print(f'{src_file} failed, program size or not found', flush=True)
        return -1
    
    if YARP_SAN_FILE:
        san_ret = sanitize_check(src_file, '', tmp_dir)
        if san_ret == -1:
            print(f'{src_file} failed, sanitization', flush=True)
            return -1
    
    return src_file

def generate_program(tmp_dir, generator="csmith", seed=None):
    """
    Generate a program using the specified generator.
    
    Args:
        tmp_dir (str): Directory to store the generated program
        generator (str): Generator to use ("csmith" or "yarpgen")
        seed (int, optional): Random seed for generation. If None, a random seed will be used.
    
    Returns:
        str: Path to the generated source file, or -1 if generation failed
    """
    if seed is None:
        seed = random.randint(0, 9999999999)
    
    # Ensure tmp_dir exists
    os.makedirs(tmp_dir, exist_ok=True)
    
    if generator.lower() == "csmith":
        return gen_program(seed, tmp_dir)
    elif generator.lower() == "yarpgen":
        return generate_program_yarpgen(tmp_dir, seed)
    else:
        print(f"Unknown generator: {generator}", flush=True)
        return -1
