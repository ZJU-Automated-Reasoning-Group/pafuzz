import random
import os
import shutil
import subprocess
from .config import (CSMITH, CSMITH_HOME, CSMITH_TIMEOUT, MIN_PROGRAM_SIZE,
                    YARPGEN, YARPGEN_TIMEOUT)
from .utils import run_cmd, sanitize_check

def gen_program(seed, tmp_dir):
    binary_opts = ['--float', '--enable-builtin-kinds k1,k2']

    num_opts = {
        '--inline-function-prob': [1, 100],
        '--max-array-dim': [1, 6],
        '--max-array-len-per-dim': [1, 20],
        '--max-block-depth': [1, 10],
        '--max-block-size': [1, 8],
        '--max-expr-complexity': [1, 20],
        '--max-funcs': [1, 20],
        '--max-pointer-depth': [1, 4],
        '--max-struct-fields': [1, 20],
        '--max-union-fields': [1, 10],
        '--builtin-function-prob': [1, 100]
    }

    gen_command = f'{CSMITH} --concise --seed {random.randint(0, 9999999999)}'
    
    for bin_o in binary_opts:
        if 'enable' in bin_o:
            if random.randint(0, 1):
                gen_command = f'{gen_command} {bin_o}'
            else:
                bin_o = bin_o.replace('enable', 'disable')
                gen_command = f'{gen_command} {bin_o}'
        else:
            if random.randint(0, 1):
                gen_command = f'{gen_command} {bin_o}'
            else:
                bin_o = f'{bin_o[:2]}no-{bin_o[2:]}'
                gen_command = f'{gen_command} {bin_o}'

    for key, value in num_opts.items():
        num = random.randint(value[0], value[1])
        gen_command = f'{gen_command} {key} {num}'

    gen_command = f'{gen_command} -o {tmp_dir}/{seed}.c'
    
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
