#!/usr/bin/env python3
import os
import sys
from multiprocessing.pool import ThreadPool
import subprocess
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

time_cost = {}
tool_performance = {}
count_pointsto = {}

status_map = {}


def isfloat(value):
    try:
        float(value)
        return True
    except ValueError:
        return False


def get_running_status(orig) -> str:
    analysis_time = float(subprocess.check_output(['tail', '-1', orig]))
    if analysis_time >= 86400:
        status_map[orig] = "TO"
        return "TO"
    if orig not in status_map:
        with open(orig) as f:
            for line in f:
                if "std::bad_alloc" in line or "out of memory" in line:
                    status_map[orig] = "OOM"
                    return "OOM"
                elif ("Assertion" in line and "failed" in line) or "Segment" in line or "LLVM ERROR" in line:
                    status_map[orig] = "Crash"
                    return "Crash"
        with open(orig) as f:
            s = f.read()
            if s.count("\n") + 1 <= 5:
                if "Function Pointer Targets" in s:
                    pass
                elif analysis_time < 100:  # A temporarily solution
                    # print(orig, s.count("\n"))
                    status_map[orig] = "Crash"
                    return "Crash"
                else:
                    status_map[orig] = "OOM"
                    return "OOM"
        return ""
    return status_map[orig]


def time_stats(proj, tool, orig):
    analysis_time = float(subprocess.check_output(['tail', '-1', orig]))
    if proj not in time_cost:
        time_cost[proj] = {tool: f'{analysis_time:.2f}' if analysis_time < 86400 else "TO"}
    elif tool not in time_cost[proj]:
        time_cost[proj][tool] = f'{analysis_time:.2f}' if analysis_time < 86400 else "TO"
    elif isfloat(time_cost[proj][tool]) and analysis_time > float(time_cost[proj][tool]):
        if analysis_time < 86400:
            time_cost[proj][tool] = str(float(time_cost[proj][tool]) + float(f'{analysis_time:.2f}'))
        else:
            time_cost[proj][tool] = "TO"
    if get_running_status(orig) != "":
        time_cost[proj][tool] = get_running_status(orig)
    # if "imagick" in orig: print(time_cost[proj][tool], analysis_time, orig, time_cost[proj][tool], isinstance(
    # time_cost[proj][tool], str), analysis_time > float(time_cost[proj][tool]))


def performance_stats(proj, tool, orig, res):
    with open(res) as f:
        if os.stat(res).st_size == 0:
            res = {}
        else:
            res = json.loads(f.read())
        num_callsites = 0
        num_resolved = 0
        for callsite, ptinfo in res.items():
            num_callsites += 1
            if len(ptinfo["pointsto"]) > 0:
                num_resolved += 1
    if proj not in tool_performance:
        tool_performance[proj] = {tool: [num_resolved, num_callsites, ""]}
    elif tool not in tool_performance[proj]:
        tool_performance[proj][tool] = [num_resolved, num_callsites, ""]
    else:
        tool_performance[proj][tool][0] += num_resolved
        tool_performance[proj][tool][1] += num_callsites
    tool_performance[proj][tool][2] = get_running_status(orig)
    pass


def count_stats(proj, tool, orig, res):
    with open(res) as f:
        if os.stat(res).st_size == 0:
            res = {}
        else:
            res = json.loads(f.read())
        zero_pointsto = 0
        one_pointsto = 0
        two_pointsto = 0
        # three_pointsto = 0
        more_pointsto = 0
        for callsite, ptinfo in res.items():
            if len(ptinfo["pointsto"]) == 0:
                zero_pointsto += 1
            elif len(ptinfo["pointsto"]) == 1:
                one_pointsto += 1
            elif len(ptinfo["pointsto"]) == 2:
                two_pointsto += 1
            # elif len(ptinfo["pointsto"]) == 3:
            #     three_pointsto += 1
            elif len(ptinfo["pointsto"]) >= 3:
                more_pointsto += 1
    if proj not in count_pointsto:
        count_pointsto[proj] = {tool: [zero_pointsto, one_pointsto, two_pointsto, more_pointsto, ""]}
    elif tool not in count_pointsto[proj]:
        count_pointsto[proj][tool] = [zero_pointsto, one_pointsto, two_pointsto, more_pointsto, ""]
    else:
        count_pointsto[proj][tool][0] += zero_pointsto
        count_pointsto[proj][tool][1] += one_pointsto
        count_pointsto[proj][tool][2] += two_pointsto
        count_pointsto[proj][tool][3] += more_pointsto
    count_pointsto[proj][tool][4] = get_running_status(orig)
    pass


def worker(res):
    raw_txt = res.replace(".json", ".txt")
    res_arr = res.split("/")
    proj_name = res_arr[-2]
    tool_name = "_".join(res_arr[-1].split(".")[-3:-1])
    time_stats(proj_name, tool_name, raw_txt)
    performance_stats(proj_name, tool_name, raw_txt, res)
    count_stats(proj_name, tool_name, raw_txt, res)

    pass


def print_to_csv():
    mode_list = ["DSA_dsa", "PHASAR_cha", "PHASAR_dta",
                 "PHASAR_otf", "SVF_ander", "SVF_type", "SVF_diff", "SVF_wave",
                 "SVF_fs", "SVF_hybrid", "SVF_hybridlazy", "SVF_lazy", "SVF_selective", "SVF_sfrander", "SVFDVF_cxt",
                 "SVFDVF_dfs",
                 "CANARY_dyck"]

    s = 'project,' + ','.join(mode_list) + "\n"
    for proj, tool_res in time_cost.items():
        s += proj
        for mode in mode_list:
            if mode in tool_res:
                s += ","
                if isfloat(tool_res[mode]):
                    s += f'{float(tool_res[mode]):.2f}'
                else:
                    s += tool_res[mode]
            else:
                s += ",OOM"
        s += "\n"

    with open('time_stats.csv', 'w+') as f:
        f.write(s)

    s = 'project,' + ','.join(mode_list) + "\n"
    for proj, tool_res in tool_performance.items():
        s += proj
        for mode in mode_list:
            if mode in tool_res:
                s += "," + str(tool_res[mode][0]) + '/' + str(tool_res[mode][1])
                if len(tool_res[mode][2]) > 0:
                    s += "(" + tool_res[mode][2] + ")"
            else:
                s += ",OOM"
        s += "\n"

    with open('perf_stats.csv', 'w+') as f:
        f.write(s)

    s = 'project,' + ','.join(mode_list) + "\n"
    for proj, tool_res in count_pointsto.items():
        s += proj
        for mode in mode_list:
            if mode in tool_res:
                s += "," + str(tool_res[mode][0]) + '/' + str(tool_res[mode][1]) + '/' + str(
                    tool_res[mode][2]) + '/' + str(tool_res[mode][3])
                if len(tool_res[mode][4]) > 0:
                    s += "(" + tool_res[mode][4] + ")"
            else:
                s += ",OOM"
        s += "\n"
    with open('count_stats.csv', 'w+') as f:
        f.write(s)


def data_fix():
    with open('time_stats.csv', 'w+') as f:
        # new_s = ""
        # for line in f:
        #     proj_res = line.split(",")
        #     update_map = {}
        #     should_update = False
        #     for time in proj_res[1:]:
        #         if float(time) > 5:
        #             should_update = True
        #     if should_update:
        #         new_res = ""
        #         new_s += proj_res[0]
        #         for idx, time in enumerate(proj_res[1:]):
        #             if float(time) < 1:
        #                 new_s += ",OOM"
        #             else:
        #                 new_s += "," + time
        #     else:
        #         new_s += line
        # f.write(new_s)
        pass
    with open('perf_stats.csv', 'w+') as f:
        pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--dir", help="Specifies input directory for json results", required=True)
    args = parser.parse_args()

    pool = ThreadPool(processes=20)

    reslist = [f for f in glob.glob(args.dir + '/**/*.json', recursive=True)]

    for _ in tqdm.tqdm(pool.imap_unordered(worker, reslist), total=len(reslist)):
        pass

    # for srctxt in tqdm.tqdm(reslist):
    #     worker(srctxt)

    pool.close()
    pool.join()

    print_to_csv()

    pass
