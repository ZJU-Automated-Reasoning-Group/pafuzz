"""
Differential Testing for Pointer Analyses
"""
import argparse
import configparser
import logging
import os
import shutil
import signal
import subprocess
import sys
import time
from dataclasses import dataclass
from multiprocessing.pool import Pool
from pathlib import Path
from threading import Timer
from typing import List, Optional

from generator_new import CSourceGenerator

from generator_new import gencsmith

parser = argparse.ArgumentParser()
parser.add_argument('--input', dest='input', type=str)
parser.add_argument('--output', dest='output', default='/tmp/z3-res9', type=str)
parser.add_argument('--timeout', dest='timeout', default=10, type=int, help="timeout for each solving")
parser.add_argument('--count', dest='count', default=1000, type=int, help="counts for each combination")
parser.add_argument('--workers', dest='workers', default=1, type=int, help="num threads")
parser.add_argument('--config', dest='config', default='no', type=str)
parser.add_argument('--seed', dest='seed', default='no', type=str)

parser.add_argument("-v", "--verbose", help="increase output verbosity",
                    action="store_true")

args = parser.parse_args()
if args.verbose:
    logging.basicConfig(level=logging.DEBUG)
m_num_process = args.workers  # thread

m_tools = [
    # '/home/work/SVF/build/bin/saber --stat=false -uaf',
    # '/home/work/SVF/build/bin/dvf -cxt --query=all --stat=false',
    # '/home/work/SVF/build_asan/bin/wpa --sfrander -stat=false',
    '/home/work/SVF/build_asan/bin/wpa -lander --print-pts -stat=false',
    '/home/work/SVF/build_asan/bin/wpa -wander --print-pts -stat=false',
    '/home/work/SVF/build_asan/bin/wpa -hlander --print-pts -stat=false',
    # '/home/work/SVF/build_asan/bin/wpa -fspta -stat=false',
    # '/home/work/SVF/build/bin/wpa --fstbhc -stat=false -svfg',
    # '/home/work/sea-dsa/build/bin/seadsa --sea-dsa=butd-cs --sea-dsa-aa-eval',
    # '/home/work/phasar/build_asan/tools/phasar-llvm/phasar-llvm --pointer-analysis=CFLAnders ifds-lca -m',
    # '/home/work/phasar/build_asan/tools/phasar-llvm/phasar-llvm --pointer-analysis=CHA -m',
    # '/home/work/phasar/build_asan/tools/phasar-llvm/phasar-llvm --call-graph-analysis=RTA -m',
    # '/home/work/phasar/build_asan/tools/phasar-llvm/phasar-llvm --call-graph-analysis=DTA -m',
    # '/home/work/phasar/build_asan/tools/phasar-llvm/phasar-llvm --call-graph-analysis=VTA -m',
    # '/home/work/phasar/build_asan/tools/phasar-llvm/phasar-llvm --call-graph-analysis=OTF -m',
]

# m_compiler = '/home/work/llvm/llvm3.6/build/release+asserts/bin/clang'
m_compiler = '/home/work/llvm10/llvm/build_debug/bin/clang'

if args.config != 'no':
    m_config = configparser.ConfigParser()
    m_config.read(args.config)
    m_compiler = m_config['DIFFPTS']['Compiler']


def find_bc(path):
    files_list = []  # path to smtlib2 files
    for root, dirs, files in os.walk(path):
        for fname in files:
            if os.path.splitext(fname)[1] == '.bc':
                files_list.append(os.path.join(root, fname))
    return files_list


def split_list(alist, wanted_parts=1):
    length = len(alist)
    return [alist[i * length // wanted_parts: (i + 1) * length // wanted_parts]
            for i in range(wanted_parts)]


in_dir = args.input
out_dir = args.output
timeout = args.timeout
count = args.count

shutil.rmtree(out_dir)
os.mkdir(out_dir)

m_use_black_list = True
black_list = []
bf = open('black_list', 'r')
if m_use_black_list:
    for line in bf:
        black_list.append(line.replace("\n", ""))

crashes = out_dir + '/crash'
inputs = out_dir + '/input'
os.mkdir(crashes)
os.mkdir(inputs)


def terminate(process, is_timeout):
    if process.poll() is None:
        try:
            process.terminate()
            is_timeout[0] = True
        except Exception as e:
            print("error for interrupting")
            print(e)


def work(idt):
    """
    use csmith to generate C programs continuously, and run the analyzers on each of the generated program
    """
    log = open(out_dir + '/test-' + str(idt) + '_' + str(time.time()) + '--' + str(timeout) + '--' + str(count),
               'w')
    counter = 0
    while True:
        try:
            if counter % count == 0:
                logging.debug("enter parameter generations")
                counter = 0

            name = '/diff_input-' + str(idt) + "_" + str(counter) + '.c'
            tmp_file = inputs + name

            counter += 1

            logging.debug("Enter constraint generation")

            ret_st = gencsmith(tmp_file)  # C file generatgor
            if ret_st != 0:
                continue
            if os.stat(tmp_file).st_size == 0:
                print("tmp file empty")

            logging.debug(tmp_file)

            # TODO: we need to generate llvm bitcode
            compiler_cmd = [m_compiler, '-I/home/work/csmith/runtime', '-emit-llvm', '-g', '-c', tmp_file, '-o',
                            tmp_file + ".bc"]
            # compiler_cmd.append('-O3')

            logging.debug("Enter bitcode generation")
            p = subprocess.run(compiler_cmd, capture_output=True, timeout=35)
            # TODO: check the return code

            if os.path.isfile(tmp_file):
                os.remove(tmp_file)

            tmp_file_bc = tmp_file + ".bc"
            if not os.path.isfile(tmp_file_bc):
                continue
            # print(tmp_file)

            m_res = []
            for _ in m_tools:
                m_res.append('unknown')

            m_res_out = []

            for tool in m_tools:
                cmd_tool = []
                for cc in tool.split(' '):
                    cmd_tool.append(cc)

                cmd_tool.append(tmp_file_bc)
                logging.debug(cmd_tool)
                logging.debug(tool)
                logging.debug(" start to analyze")
                ptool = subprocess.Popen(cmd_tool, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                is_timeout = [False]
                timertool = Timer(3600, terminate, args=[ptool, is_timeout])
                timertool.start()
                out_tool = ptool.stdout.readlines()
                out_tool = ' '.join([str(element.decode('UTF-8')) for element in out_tool])
                logging.debug(out_tool)

                if not is_timeout[0]:  # do not add timeout case
                    # TODO: keep unknown for finding performance issues
                    bl_msg = ['Assertion', 'Santizer', 'PrintStackTrace', 'Segment']
                    toadd = True
                    for bl in bl_msg:
                        if bl in out_tool:
                            flag = 1
                            for item in black_list:
                                if item in out_tool:
                                    flag = 0
                                    break
                            if flag == 1:
                                print("find error!")
                                shutil.copy(tmp_file_bc, out_dir + "/crash")
                                print(tmp_file_bc)

                    if "Assertion" in out_tool or "Santizer" in out_tool or "error" in out_tool:
                        toadd = False

                    if toadd:
                        m_res_out.append(out_tool)
                # close?
                ptool.stdout.close()
                timertool.cancel()

                # logging.debug("Results: ")
            # decide if the elements of the list are equal (solving results are identical)
            if 2 <= len(m_res_out) != m_res_out.count(m_res_out[0]):
                print("find inconsistency!")
                shutil.copyfile(tmp_file_bc, crashes + name + ".bc")
                print(tmp_file_bc)
            else:
                if os.path.isfile(tmp_file_bc):
                    os.remove(tmp_file_bc)
                if os.path.isfile(tmp_file + ".wpa"):
                    os.remove(tmp_file + ".wpa")  #
        except Exception as e:
            # remove file?
            print(e)
    log.close()
    print("We are finish here, have a good day!")


def solve_seed(flist: List):
    """
    Run the analyzers on a set of bitcodes
    TODO: currently, we do not apply mutations on the seeds
    """
    for tmp_file in flist:
        name = tmp_file
        try:
            for tool in m_tools:
                cmd2 = []
                for cc in tool.split(' '):
                    cmd2.append(cc)
                cmd2.append(tmp_file)
                logging.debug(cmd2)
                # print(cmd2)
                logging.debug("Start to solve")
                p = subprocess.Popen(cmd2, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                is_timeout = [False]
                # run the analyzers using a time limit of 3600 seconds
                timer = Timer(3600, terminate, args=[p, is_timeout])
                timer.start()
                out = p.stdout.readlines()
                out = ' '.join([str(element.decode('UTF-8')) for element in out])
                logging.debug(out)
                flag = 0  # if flag = 1, then there are some errors in the output of the tool
                # some function are called xxerror
                err_msg = ['Assertion', 'Santizer', 'PrintStackTrace', 'Segment']
                for item in err_msg:
                    if item in out:
                        flag = 1
                        break

                if flag == 1:
                    for black in black_list:
                        if black in out:
                            flag = 0
                            break
                if flag == 1:
                    print("find!")
                    print(out)
                    print(cmd2)
                    print(name)
                    # print("file ", tmp_file, " dst: ", out_dir + "/crash")
                    # shutil.copy(tmp_file, out_dir + "/crash")
                p.stdout.close()  # close?
                timer.cancel()
        except Exception as e:
            print(e)


# initialize the thread pool
tp = Pool(m_num_process)


def signal_handler(sig, frame):
    tp.terminate()
    print("We are finish here, have a good day!")
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)

"""
There are two modes
- args.seed == no: use csmith to generate C programs continuously, 
                   and run the analyzers on each of the generated program
- args.seed == yes: run the analyzers on a set of bitcodes (e.g., generated from real-world programs)
"""
if args.seed == 'no':
    for i in range(m_num_process):
        tp.apply_async(work, (i,))
    tp.close()
    tp.join()

else:
    flist = find_bc(args.seed)
    print("Num Seed: ", len(flist))
    files = split_list(flist, m_num_process)
    for i in range(0, m_num_process):
        tp.apply_async(solve_seed, args=(files[i],))

    tp.close()
    tp.join()
