#!/usr/bin/env python3
# import os
# import sys
from multiprocessing.pool import ThreadPool
# import subprocess
# from threading import Timer
import argparse
import glob
import tqdm
# import errno
# import pathlib
# from shutil import copyfile
# import time
# import resource
import json
import re


def isfloat(value):
    try:
        float(value)
        return True
    except ValueError:
        return False


def isint(value):
    try:
        int(value)
        return True
    except ValueError:
        return False


class LogAnalyzer(object):
    def __init__(self, srcfile):
        super().__init__()
        self.srcfile = srcfile
        self.pointstoset = {}

    def print_to_json(self):
        with open(self.srcfile.replace("txt", "json"), "w+") as f:
            f.write(json.dumps(self.pointstoset, indent=4))


class SVFLogAnalyzer(LogAnalyzer):
    def parse(self):
        with open(self.srcfile) as f:
            stats_time = 0
            while True:
                line = f.readline()
                # line2 = f.readline()
                # # print(line, line2, len(line))
                if "Function Pointer Targets" in line:
                    stats_time += 1
                    self.pointstoset = {}
                if not line:
                    break  # EOF
                if line.startswith("NodeID:"):
                    node_id = int(line.split(" ")[1])
                    pointstoset = []
                    linenum = -1
                    file = None
                    callsite = None
                elif line.startswith("CallSite:"):
                    # print(line)
                    callsiteinfo = line.split("CallSite:   ")[1].split("\t with Targets: ")[0].strip()
                    # callsite = callsiteinfo.split("\tLocation: ")[0]
                    if not callsiteinfo.endswith("}"):
                        # print(line, line2, callsiteinfo)
                        # print(line2, "Location: " not in line2)
                        line2 = f.readline()
                        if not line2:
                            break  # EOF
                        while "Location: " not in line2:
                            line2 = f.readline()
                            if not line2:
                                # print(self.srcfile)
                                break  # EOF
                        else:
                            callsite = callsiteinfo + line2.split("\tLocation: ")[0]
                            loc = line2.split("\tLocation: ")[1]
                    else:
                        try:
                            callsite = callsiteinfo.split("\tLocation: ")[0]
                            loc = callsiteinfo.split("\tLocation: ")[1]
                        except Exception as e:
                            print(callsiteinfo, self.srcfile)
                            raise e
                    linenum = int(loc.split(" ")[2])
                    file = loc.split(" ")[4]
                elif line.startswith("\t") and not line.startswith("\t!!!"):
                    pointstoset.append(line.split("\t")[1].strip())
                elif line in ['\n', '\r\n']:
                    # print(line2)
                    if "node_id" in vars() and "callsite" in vars() and callsite is not None:
                        if callsite not in self.pointstoset:
                            self.pointstoset[callsite] = {
                                "pointsto": pointstoset,
                                "line": linenum,
                                "file": file,
                                "id": node_id
                            }
                        else:
                            self.pointstoset[callsite]["pointsto"] += pointstoset
                            self.pointstoset[callsite]["pointsto"] = [i for n, i in
                                                                      enumerate(self.pointstoset[callsite]["pointsto"]) \
                                                                      if
                                                                      i not in self.pointstoset[callsite]["pointsto"][
                                                                               n + 1:]]
        pass


class PHASARLogAnalyzer(LogAnalyzer):
    def parse(self):
        with open(self.srcfile) as f:
            while True:
                line = f.readline()
                if not line:
                    break
                if line.startswith("CallSite:"):
                    callsite = line.split("CallSite:\t")[1].split(", !psr")[0].strip()
                elif line.startswith("Points-to:"):
                    pointstoset = line.split("Points-to:\t")[1].strip().split(" ")
                    if pointstoset == [""]:
                        pointstoset = []
                    self.pointstoset[callsite] = {
                        "pointsto": pointstoset,
                    }
        pass


class DSALogAnalyzer(LogAnalyzer):
    def parse(self):
        with open(self.srcfile) as f:
            while True:
                line = f.readline()
                if not line:
                    break
                done = False
                if "call" in line and "(" in line and ")" in line and "Callees:" not in line:
                    if " at " in line:
                        callsite = line.split(" at ")[0].strip()
                        try:
                            loc = line.split(" at ")[1].strip().split(" ")[0]
                        except Exception as e:
                            print(callsite)
                            raise e
                        if "UNRESOLVED" in line:
                            pointstoset = []
                            done = True
                    elif " at " not in line:
                        line2 = f.readline()
                        if not line2:
                            break
                        callsite = line.strip() + line2.split(" at ")[0].strip()
                        try:
                            loc = line2.split(" at ")[1].strip().split(" ")[0]
                        except Exception as e:
                            print(callsite)
                            raise e
                        if "UNRESOLVED" in line2:
                            pointstoset = []
                            done = True
                    file = loc.split(":")[0]
                    linenum = int(loc.split(":")[1])
                elif "Callees:" in line:
                    calleelist = line.split("Callees:{")[1].strip().split("}")[0].strip()
                    pointstoset = re.sub(r"\(.*?\)", "",
                                         calleelist.replace("i64 ", "").replace("i32 ", "").replace("i8 ", "").replace(
                                             "void ", "")).split(",")
                    done = True
                if done:
                    self.pointstoset[callsite] = {
                        "pointsto": pointstoset,
                        "line": linenum,
                        "file": file,
                    }
        pass


class CANARYLogAnalyzer(LogAnalyzer):
    def parse(self):
        with open(self.srcfile) as f:
            start = False
            while True:
                line = f.readline()
                if not line:
                    break
                done = False
                if "CallInst:   " in line:
                    callsite = line.split("CallInst:   ")[1].strip()
                    self.pointstoset[callsite] = {}
                    pointstoset = []
                    start = True
                elif isint(line):
                    pass
                elif line.strip() and start:
                    pointstoset.append(line.strip())
                elif line in ['\n', '\r\n'] and start:
                    done = True
                    start = False
                if done:
                    self.pointstoset[callsite] = {
                        "pointsto": pointstoset
                    }
        pass


def worker(file):
    fileextlist = file.split(".")
    tool = fileextlist[-3]
    if tool == "SVF" or tool == "SVFDVF":
        analyzer = SVFLogAnalyzer(file)
    elif tool == "PHASAR":
        analyzer = PHASARLogAnalyzer(file)
    elif tool == "DSA":
        analyzer = DSALogAnalyzer(file)
    elif tool == "CANARY":
        analyzer = CANARYLogAnalyzer(file)
    else:
        print("something wrong with " + file)
        exit(-1)

    analyzer.parse()
    analyzer.print_to_json()
    pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    # parser.add_argument("-t", "--tool", nargs='+', help="Specifies which tool(s) to run", required=False,
    # default=[ "all" ]) parser.add_argument("-m", "--mode", nargs='+', help="Specifies pointer analysis(es) modes",
    # required=False, default=[ "all" ])
    parser.add_argument("-d", "--dir", help="Specifies input directory for results", required=True)
    # parser.add_argument("-o", "--out", help="Specifies output directory", required=False, default="./tmp")
    args = parser.parse_args()

    srctxtlist = [f for f in glob.glob(args.dir + '/**/*.txt', recursive=True)]

    pool = ThreadPool(processes=10)

    for _ in tqdm.tqdm(pool.imap_unordered(worker, srctxtlist), total=len(srctxtlist)):
        pass

    # for srctxt in tqdm.tqdm(srctxtlist):
    #     worker(srctxt)

    pool.close()
    pool.join()

    pass
