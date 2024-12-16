#!/usr/bin/env python3
import os
import sys
from multiprocessing.pool import ThreadPool
import subprocess
from threading import Timer
import argparse
import glob
import tqdm
import errno
# import pathlib
# from shutil import copyfile
import time
import resource
from jsmin import jsmin
import json
import re
from pathlib import Path


def limit_memory(maxsize, hardmax=resource.RLIM_INFINITY):
    # soft, hard = resource.getrlimit(resource.RLIMIT_AS)
    resource.setrlimit(resource.RLIMIT_AS, (maxsize, hardmax))


class Logger(object):
    def __init__(self, filename):
        self.terminal = sys.stdout
        self.log = open(filename, "a")

    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)

    def flush(self):
        # this flush method is needed for python 3 compatibility.
        # this handles the flush command by doing nothing.
        # you might want to specify some extra behavior here.
        pass


def terminate(process):
    if process.poll() is None:
        try:
            process.terminate()
        except EnvironmentError:
            pass  # ignore


def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


def safe_open_w(path):
    """ Open "path" for writing, creating any parent directories as needed.
    """
    mkdir_p(os.path.dirname(path))
    return open(path, 'w')


def guess_proj_name(path):
    dirs = path.split("/")
    for d in dirs:
        if re.match(r"^\d{3}\.\w+_\w{1,2}$", d):
            return d.split(".")[1].split("_")[0]


def worker(pack):
    toolbin = pack[0]
    filename = pack[1]
    modearg = pack[2]
    toolname = pack[3]
    modename = pack[4]
    outdir = pack[5]

    cmd = toolbin.split(" ") + [filename] + modearg.split(" ")
    cmd = list(filter(None, cmd))
    print(cmd)

    logger = Logger("info.log")
    result_logger = Logger("err.log")
    exp_logger = Logger("exp.log")

    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            preexec_fn=limit_memory(40 * 1024 * 1024 * 1024))
    start_time = time.time()
    timer = Timer(24 * 3600, terminate, args=[proc])
    timer.start()
    output, err = proc.communicate(b"input data that is passed to subprocess' stdin")
    # print(' '.join(cmd), err.decode())
    rc = proc.returncode
    # print(filename.split("/")[-3] + "/" + filename.split("/")[-1] + ".txt")
    with safe_open_w(os.path.join(outdir, guess_proj_name(filename) + "/" + filename.split("/")[
        -1] + "." + toolname + "." + modename + ".txt")) as f:
        f.write(output.decode("utf-8") + err.decode("utf-8") + "\n")
        f.write(str(time.time() - start_time))
    timer.cancel()
    pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--tool", type=str, nargs='+', help="Specifies which tool(s) to run", required=False,
                        default=["SVF", "SVFDVF", "PHASAR", "DSA"])
    parser.add_argument("-m", "--mode", type=str, nargs='+', help="Specifies pointer analysis(es) modes",
                        required=False, default=["all"])
    parser.add_argument("-d", "--dir", type=str, nargs='+', help="Specifies input directory(ies) for bitcodes",
                        required=True)
    parser.add_argument("-o", "--out", help="Specifies output directory", required=False, default="./tmp")
    parser.add_argument("-n", "--num", type=int, help="Number of threads to run PTAs", required=False, default=10)
    args = parser.parse_args()

    with open('ptaconfig.jsonc') as js_file:
        minified = jsmin(js_file.read())
    ptaconfig = json.loads(minified)
    tools = ptaconfig["tools"]
    modes = ptaconfig["modes"]

    pool = ThreadPool(processes=args.num)

    # print(args.dir)
    bclist = [f for d in args.dir for f in glob.glob(d + '/**/*.bc', recursive=True)]
    # print(bclist)
    tool_list = args.tool if args.tool != ["all"] else tools.keys()
    mode_list = args.mode if args.mode != ["all"] else [mode for tool, mode_pair in modes.items() for mode in mode_pair]
    print(mode_list)
    # print(tool_list)

    tool_cmd_list = {}
    for tool in tool_list:
        tool_cmd_list = dict(tool_cmd_list, **{tool: tools[tool]})
    print(tool_cmd_list)

    tasks = []
    proj_cache = []

    for f in bclist:
        proj_name = guess_proj_name(f)
        if proj_name in proj_cache:
            continue
        proj_cache.append(proj_name)
        for tool, mode_pair in modes.items():
            print(tool, tool in tool_list)
            if tool in tool_list:
                for mode in mode_list:
                    if mode in mode_pair:
                        tasks += [(tool_cmd_list[tool].replace("~", str(Path.home())), f, mode_pair[mode], tool, mode,
                                   args.out)]
                        # print([ tool_cmd_list[tool], f, mode_pair[mode] ])

    # tasks = [ (args.tool, args.mode, f, args.out) for f in glob.glob(args.directory + '/**/*.bc', recursive=True) ]

    for _ in tqdm.tqdm(pool.imap_unordered(worker, tasks), total=len(tasks)):
        pass

    pool.close()
    pool.join()
    pass
