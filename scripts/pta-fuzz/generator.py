"""
C/C++ source code generator. Currently, we use csmith and only generate .c file

To generate the LLVM bitcode of a c file fname.c, you may try:
  clang -emit-llvm -g  -o fname.bc -c fname.c
"""

# import os
import subprocess
# import time
# import argparse
import random
# import shutil
# import sys
# import itertools
# import signal
import logging

m_generator = '/home/work/csmith/src/csmith'  # query generator

"""
Swarm testing: controlling different options of csmith to generate diverse programs
"""
all_swarm_opts = [
    "arrays",
    "checksum",
    "comma-operators",
    "compound-assignment",
    "consts",
    "divs",
    "embedded-assigns",
    "jumps",
    "longlong",
    "force-non-uniform-arrays",
    "math64",
    "builtins",
    "muls",
    "packed-struct",
    "paranoid",
    # "pointers",
    "structs",
    "volatiles",
    "volatile-pointers",
    "arg-structs",
    "dangling-global-pointers",
]


def checkUB(cfilename: str):
    """
    Check whether the generated C program has undefined behavior
    Currently, we do not use this function
    """
    clangfc = "/usr/bin/clang -msse4.2 -m64 -I/home/work/csmith/runtime -O0 -fsanitize=undefined"
    timeout = "timeout"
    filename = cfilename
    # filename=cfilename.split(".")[0]
    exe = filename + "exe-clang"
    out = filename + "out-clang"
    rm_cmd = ["rm", "-f", "-o", exe, cfilename]
    # subprocess.call(rm_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    # compile_cmd = "timeout -s 9 5".split()
    compile_cmd = "timeout 30s".split()
    compile_cmd.extend(clangfc.split())
    compile_cmd.extend(["-c", cfilename, "-o", exe])
    print(compile_cmd)
    cplt = subprocess.run(compile_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if cplt.returncode != 0:
        print("Seed Program Generation: cannot compile")
        return 2
    run_cmd = "timeout 30s".split()
    run_cmd.append("./" + exe)
    with open(out, "w") as outf:
        cplt = subprocess.run(run_cmd, stdout=outf, stderr=subprocess.DEVNULL)
        if cplt.returncode != 0:
            print("Seed Program Generation: exe timeout")
            subprocess.call(rm_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return 3

    rterrorflag = False
    with open(out, "r") as outf:
        for line in outf:
            if line.find("runtime error") >= 0:
                print("Seed Program Generation: runtime error in exe")
                rterrorflag = True
                break

    subprocess.call(rm_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if rterrorflag:
        return 1
    else:
        return 0


def gencsmith(cfilename: str):
    """
    Run csmith to generate a C program (and write the program to cfilename
    """
    # TODO: should we always use the extra?
    extra = "--pointers --no-unions --safe-math --no-argc --no-inline-function --no-bitfields --no-return-structs " \
            "--quiet --concise"
    swarm_opt = ""
    for opt in all_swarm_opts:
        # add options in all_swarm_opts
        p = random.randint(0, 99) / 100
        if p < 0.5:
            swarm_opt = swarm_opt + " --" + opt + " "
        else:
            swarm_opt = swarm_opt + " --no-" + opt + " "
    # logging.debug(swarm_opt)
    csmith_cmd = [m_generator]
    csmith_cmd.extend(swarm_opt.split())
    csmith_cmd.extend(extra.split())
    csmith_cmd.extend('--max-pointer-depth 6'.split())
    logging.debug(csmith_cmd)
    with open(cfilename, "w") as cfile:
        subprocess.call(csmith_cmd, stdout=cfile)  # TODO: timeout for csmith?
        # check ub
        # ret = checkUB(cfilename)  # TODO: check ub
        # if ret != 0:
        #    return ret
        # check size
        # minsize = 4000
        # filesize = os.path.getsize(cfilename)
        # if filesize < minsize:
        #    print("Seed Program Generation: generated C file too small")

        # print("Seed Program Generation: have a good seed file")
        return 0