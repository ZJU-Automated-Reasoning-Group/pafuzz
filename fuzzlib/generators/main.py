import os
import signal
import psutil
import itertools
import tempfile
import shutil
from . import config
from .sanitizer_utils import (choose_gcc_sanitizer, choose_gcc_sanitizer_attr,
                            choose_llvm_sanitizer, choose_llvm_sanitizer_attr)
from .optimization_utils import (choose_gcc_optimization, choose_llvm_optimization)
from .parsing_utils import parse_ast, parse_ast_clang, parse_run_option
from .program_generation import gen_program
from .file_utils import (find_c_files, clear_path, merge_files, generate)

def kill_process(p):
    try:
        p.send_signal(signal.SIGKILL)
    except psutil.NoSuchProcess:
        pass

def kill_all(pid):
    try:
        parent = psutil.Process(pid)
        children = parent.children(recursive=True)
    except psutil.NoSuchProcess:
        return
    for p in children:
        kill_process(p)
    kill_process(parent)

def filter_crash(info, seg):
    infos = info.split('\n')
    for l in infos:
        if seg in l:
            return l

def assign_values(elements, n):
    permutations = list(itertools.product(elements, repeat=n))
    valid_assignments = [perm for perm in permutations if len(set(perm)) > 1]
    return valid_assignments

def gen(seed_dir, seed):
    with tempfile.TemporaryDirectory() as tmp_dir:
        src_file = gen_program(seed, tmp_dir)
        if not isinstance(src_file, str):
            return -1
        seed_file = f'{seed_dir}/{seed}.c'
        shutil.copy(src_file, seed_file)
        return seed_file

def main():
    # Add your main program logic here
    pass

if __name__ == "__main__":
    main()
    