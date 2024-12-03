import glob
import itertools
import os
import random
import re
import shutil
import signal
import subprocess
import tempfile

import psutil

parse_tool = '/home/code/ParseAst/tool_all'
parse_tool_clang = '/home/code/ParseAst/tool_clang'
YARPGEN = '/home/compiler/yarpgen/build/yarpgen'
YARPGEN_TIMEOUT = 10

SAN_FILE = '/home/code/Artifact/san_check.sh'
YARP_SAN_FILE = '/home/code/Artifact/yarp_san_check.sh'
CSMITH = '/home/software/csmith/bin/csmith'
CSMITH_HOME = '/home/compiler/csmith/runtime'

PARSE_TIMEOUT = 8
CSMITH_TIMEOUT = 15
MIN_PROGRAM_SIZE = 20000
SHELL_TIMEOUT = 300
COMPILE_TIMEOUT = 30
SAN_COMPILE_TIMEOUT = 30
RUN_TIMEOUT = 15

GCC = '/home/software/gcc-trunk-3aa004f/bin/gcc'
CLANG = 'clang'


def choose_gcc_sanitizer():
    select_sans = set()
    san_list = sanitizers.gcc_san
    random.shuffle(san_list)
    for san in san_list:
        if random.choice([0, 1]):
            select_sans.add(san)
    # print(select_sans)
    exsans = set()
    for san in select_sans:
        if san in exsans:
            continue
        if san in sanitizers.gcc_exclude_san.keys():
            esan = sanitizers.gcc_exclude_san[san]
            exsans = exsans | esan
    select_sans = select_sans - exsans
    # print(select_sans)
    return list(select_sans)


def choose_gcc_sanitizer_attr(sans):
    attrs = set()
    for san in sans:
        if san in attributes.gcc_san_attributes.keys():
            attrs.add(attributes.gcc_san_attributes[san])
    return list(attrs)


def choose_llvm_sanitizer():
    select_sans = set()
    san_list = sanitizers.llvm_san
    random.shuffle(san_list)
    for san in san_list:
        if random.choice([0, 1]):
            select_sans.add(san)
    exsans = set()
    for san in select_sans:
        if san in exsans:
            continue
        if san in sanitizers.llvm_exclude_san.keys():
            esan = sanitizers.llvm_exclude_san[san]
            exsans = exsans | esan
    select_sans = select_sans - exsans
    return list(select_sans)


def choose_llvm_sanitizer_attr(sans):
    attrs = set()
    for san in sans:
        if san in attributes.llvm_san_attributes.keys():
            attrs.add(attributes.llvm_san_attributes[san])
    return list(attrs)


def choose_gcc_optimization(optimization_level):
    level_map = {
        'O0': set(),
        'O1': optimizations.option_O1,
        'O2': optimizations.option_O2,
        'Os': optimizations.option_Os,
        'O3': optimizations.option_O3,
    }
    selected_opt = level_map[optimization_level]
    remianed_opt = optimizations.option_O3 - selected_opt
    if not remianed_opt:
        return []
    random_cnt = random.randint(1, 5)
    choose_opt = random.sample(list(remianed_opt), random_cnt)
    return choose_opt


def choose_llvm_optimization():
    random_cnt = random.randint(1, 5)
    choose_opt = random.sample(optimizations.llvm_opt_pass, random_cnt)
    return choose_opt


def find_c_files(directory, file_type):
    c_files = glob.glob(f'{directory}/**/*.{file_type}', recursive=True)
    return c_files


def parse_run_option(c_file):
    compile_map = {'preprocess': '-E', 'assemble': '-S', 'compile': '-c', 'link': '', 'run': '-o'}
    # print(c_file)
    run_value, org_options_value = '', ''
    options_value = ''
    with open(c_file, 'r', encoding='ISO-8859-1') as fr:
        for line in fr:
            match_run = re.search(r'\bdo\s+(\w+)\s+\}', line)
            if match_run:
                run_value = match_run.group(1)
                # print(f'Run: {run_value}')

            match_options = re.search(r'options\s+"(.*?)"', line)
            if match_options:
                match_opt = match_options.group(1).strip()
                org_options_value = f'{org_options_value} {match_opt}'
    if '-O' in org_options_value:
        # print(options_value)
        if ' ' in org_options_value:
            vsplit = org_options_value.split()
            bak_options = []
            for option in vsplit:
                if '-O' in option:
                    continue
                bak_options.append(option)
            options_value = ' '.join(bak_options)
        else:
            options_value = ''
    else:
        options_value = org_options_value
        # print(options_value)
    if run_value:
        return compile_map[run_value], options_value, org_options_value
    else:
        return '', options_value, org_options_value


def parse_ast(c_file, option, tmp_dir):
    log_file = f"{tmp_dir}/{os.path.basename(c_file).replace('.c', '.log')}"
    try:
        parse_cmd = f'timeout {PARSE_TIMEOUT} {parse_tool} {c_file}'
        parse_p = subprocess.Popen(parse_cmd, shell=True, stdout=open(log_file, 'w+'), cwd=tmp_dir)
        parse_p.communicate(timeout=PARSE_TIMEOUT)
    except subprocess.TimeoutExpired:
        if os.path.exists(log_file):
            os.remove(log_file)
        return

    strut_var_list = []
    var_list = []
    func_list = []
    refine_list = {}
    with open(log_file, 'r') as f:
        for line in f:
            if c_file not in line:
                continue
            if 'Struct' in line:
                var_info = []
                split_info = line.strip().split(';')
                for detail_info in split_info:
                    if 'Filename' in detail_info:
                        continue
                    var_info.append(detail_info.split(':')[-1].strip())
                strut_var_list.append(var_info)
            if 'Variable' in line:
                var_info = []
                split_info = line.strip().split(';')
                for detail_info in split_info:
                    if 'Filename' in detail_info:
                        continue
                    var_info.append(detail_info.split(':')[-1].strip())
                var_list.append(var_info)
                line_num, end_col = int(var_info[-3]), int(var_info[-1])
                if line_num not in refine_list.keys():
                    refine_list[line_num] = [end_col]
                else:
                    refine_list[line_num].append(end_col)
            if 'Definition' in line:
                func_info = []
                split_info = line.strip().split(';')
                for detail_info in split_info:
                    if 'Filename' in detail_info:
                        continue
                    func_info.append(detail_info.split(':')[-1].strip())
                func_list.append(func_info)

    if os.path.exists(log_file):
        os.remove(log_file)

    if (not strut_var_list) and (not var_list) and (not func_list):
        return

    return [strut_var_list, var_list, func_list, refine_list]


def parse_ast_clang(c_file, option, tmp_dir):
    log_file = f"{tmp_dir}/{os.path.basename(c_file).replace('.c', '.log')}"
    try:
        parse_cmd = f'timeout {PARSE_TIMEOUT} {parse_tool_clang} {c_file}'
        parse_p = subprocess.Popen(parse_cmd, shell=True, stdout=open(log_file, 'w+'), cwd=tmp_dir)
        parse_p.communicate(timeout=PARSE_TIMEOUT)
    except subprocess.TimeoutExpired:
        if os.path.exists(log_file):
            os.remove(log_file)
        return

    strut_var_list = []
    var_list = []
    func_list = []
    loop_list = []
    struct_list = []
    struct_var_list = []
    refine_list = {}
    with open(log_file, 'r') as f:
        for line in f:
            if c_file not in line:
                continue
            if 'Struct' in line:
                var_info = []
                split_info = line.strip().split(';')
                if split_info[1].split(':')[-1].strip().split()[0].strip() == 'struct':
                    for detail_info in split_info:
                        if 'Filename' in detail_info:
                            continue
                        var_info.append(detail_info.split(':')[-1].strip())
                    struct_list.append(var_info)
                else:
                    for detail_info in split_info:
                        if 'Filename' in detail_info:
                            continue
                        var_info.append(detail_info.split(':')[-1].strip())
                    struct_var_list.append(var_info)
            if 'Variable' in line:
                var_info = []
                split_info = line.strip().split(';')
                for detail_info in split_info:
                    if 'Filename' in detail_info:
                        continue
                    var_info.append(detail_info.split(':')[-1].strip())
                var_list.append(var_info)
                line_num, end_col = int(var_info[-3]), int(var_info[-1])
                if line_num not in refine_list.keys():
                    refine_list[line_num] = [end_col]
                else:
                    refine_list[line_num].append(end_col)
            if 'Loop;' in line:
                split_info = line.strip().split(';')
                loop_line = split_info[-2].split(':')[-1].strip()
                loop_column = split_info[-1].split(':')[-1].strip()
                loop_info = [loop_line, loop_column]
                loop_list.append(loop_info)
            if 'Definition' in line:
                func_info = []
                split_info = line.strip().split(';')
                for detail_info in split_info:
                    if 'Filename' in detail_info:
                        continue
                    func_info.append(detail_info.split(':')[-1].strip())
                func_list.append(func_info)

    if os.path.exists(log_file):
        os.remove(log_file)

    if (not strut_var_list) and (not var_list) and (not func_list) and (not loop_list) and (not struct_list):
        return

    return [strut_var_list, var_list, func_list, loop_list, struct_list, refine_list]


def clear_path(file_path):
    dir_name = os.path.dirname(file_path)
    base_name = os.path.basename(file_path)
    reg = base_name.replace('.c', '')
    target_files = os.listdir(dir_name)
    for file in target_files:
        if file.endswith('.c') or file.endswith('.h'):
            continue
        if file.startswith(reg):
            if os.path.exists(f'{dir_name}/{file}'):
                os.remove(f'{dir_name}/{file}')


def kill_process(p):
    try:
        p.send_signal(signal.SIGKILL)
    except psutil.NoSuchProcess:
        pass


def kill_all(pid):
    try:
        parent = psutil.Process(pid)
        children = parent.children(recursive=True)
    except psutil.NoSuchProcess as exc:
        return
    for p in children:
        kill_process(p)
    kill_process(parent)


def run_cmd(cmd, timeout, work_dir=None):
    # cmd = f'timeout {int(timeout) + 1} {cmd}'
    if type(cmd) is not list:
        cmd = cmd.split(' ')
        cmd = list(filter(lambda x: x != '', cmd))
    # Start the subprocess
    if not work_dir:
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    else:
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=work_dir)
    # Wait for the subprocess to finish or timeout
    try:
        output, error = process.communicate(timeout=timeout)
        output = output.decode('utf-8', errors='ignore')
        error = error.decode('utf-8', errors='ignore')
    except subprocess.TimeoutExpired:
        # Timeout occurred, kill the process
        # os.killpg(process.pid, signal.SIGTERM)
        # process.send_signal(signal.SIGTERM)
        # process.kill()
        # cmd_str = " ".join(cmd)
        # time.sleep(1)
        # os.system(f"pkill -9 -f {cmd_str}")
        kill_all(process.pid)

        return (124, '', '')

    # Return the exit code and stdout of the process
    return (process.returncode, output, error)


def filter_crash(info, seg):
    infos = info.split('\n')
    for l in infos:
        if seg in l:
            return l


def insert(code_snippet, pos, file_name, mut_file_name, cwd):
    if pos == 0:
        pos = 1
    sed_cmd = "sed '" + str(pos) + " i\\" + code_snippet + "' " + file_name + " > " + mut_file_name
    sed_p = subprocess.Popen(sed_cmd, shell=True, cwd=cwd)
    sed_p.communicate()


def insert_org(code_snippet, pos, file_name, cwd):
    if pos == 0:
        pos = 1
    sed_cmd = "sed -i '" + str(pos) + " i\\" + code_snippet + "' " + file_name
    sed_p = subprocess.Popen(sed_cmd, shell=True, cwd=cwd)
    o, e = sed_p.communicate()
    return sed_p.returncode


def assign_values(elements, n):
    permutations = list(itertools.product(elements, repeat=n))

    valid_assignments = [perm for perm in permutations if len(set(perm)) > 1]

    return valid_assignments


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
    # gen_command = f'{CSMITH} --no-volatiles --no-volatile-pointers --no-unions  --quiet'

    # gen_command = f'{gen_command} -s {seed} -o {seed}.c'
    res = run_cmd(gen_command, CSMITH_TIMEOUT)
    if res[0] != 0:
        return -1

    src_file = f'{tmp_dir}/{seed}.c'
    # print(f'size: {os.path.getsize(src_file)}')
    if os.path.getsize(src_file) < MIN_PROGRAM_SIZE:
        print(f'{src_file} failed, program size', flush=True)
        return -1

    san_ret = sanitize_check(src_file, f'-I{CSMITH_HOME}', tmp_dir)
    if san_ret == -1:
        print(f'{src_file} failed, sanitization', flush=True)
        return -1

    return src_file


def gen(seed_dir, seed):
    # seed_dir = f'{dir}/{seed}'
    with tempfile.TemporaryDirectory() as tmp_dir:
        src_file = gen_program(seed, tmp_dir)
        if not isinstance(src_file, str):
            return -1
        seed_file = f'{seed_dir}/{seed}.c'
        shutil.copy(src_file, seed_file)
        return seed_file


def merge_files(file1, file2, output_file):
    with open(output_file, 'w') as outfile:
        with open(file1, 'r') as infile1:
            outfile.write(infile1.read())
            outfile.write("\n")

        with open(file2, 'r') as infile2:
            outfile.write(infile2.read())

    os.remove(file1)
    os.remove(file2)


def gen_yarpgen(tmp_dir, seed):
    options = {
        '--check-algo=': ['hash', 'asserts'],
        '--inp-as-args=': ['none', 'some', 'all'],
        '--emit-align-attr=': ['none', 'some', 'all'],
        # '--unique-align-size': ['true', 'false'],
        '--align-size=': ['16', '32', '64'],
        '--allow-dead-data=': ['true', 'false'],
        '--emit-pragmas=': ['none', 'some', 'all'],
        '--param-shuffle=': ['true', 'false'],
        '--expl-loop-param=': ['true', 'false'],
        # '--mutate=': ['none', 'some', 'all'],
    }

    gen_command = f'{YARPGEN} --std=c -s {random.randint(0, 9999999999)} --mutation-seed={random.randint(0, 9999999999)}'
    for key, value in options.items():
        c = random.choice(value)
        gen_command = f'{gen_command} {key}{c}'

    gen_command = f'{gen_command} -o {tmp_dir}'
    res = run_cmd(gen_command, YARPGEN_TIMEOUT)
    if res[0] != 0:
        return -1

    # pdb.set_trace()
    src_file = f'{tmp_dir}/{seed}.c'
    merge_files(f'{tmp_dir}/func.c', f'{tmp_dir}/driver.c', src_file)

    # print(f'size: {os.path.getsize(src_file)}')
    if os.path.getsize(src_file) < MIN_PROGRAM_SIZE:
        print(f'{src_file} failed, program size', flush=True)
        return -1

    san_ret = sanitize_check(src_file, f'-I{tmp_dir}', tmp_dir)
    if san_ret == -1:
        print(f'{src_file} failed, sanitization', flush=True)
        return -1

    return src_file


def san_check(san_file, src_file, tmp_dir):
    shutil.copy(san_file, tmp_dir)

    check_cmd = f'./{os.path.basename(san_file)} {src_file}'
    res = run_cmd(check_cmd, SHELL_TIMEOUT)

    if res[0] != 0:
        return -1


def form_optimization_set(set1, set2):
    all_set = []
    for o in set1:
        all_set.append(o.replace('-f', '-fno-', 1))

    return all_set + list(set2)


def filter_opt(opts):
    new_list = []
    opt_list = opts.split()
    for o in opt_list:
        if not o.startswith('-f'):
            new_list.append(o)
    return ' '.join(new_list)


def sanitize_check(src_file, comp_option, tmp_dir):
    # tmp_f = tempfile.NamedTemporaryFile(suffix=".exe", delete=False)
    # tmp_f.close()
    # out_file = tmp_f.name
    out_file = f'{tmp_dir}/san.out'
    comp_cmd = f'{GCC} {comp_option} -w -O0 -fsanitize=undefined,address,leak {src_file} -o {out_file}'
    comp_res = run_cmd(comp_cmd, SAN_COMPILE_TIMEOUT)
    # pdb.set_trace()
    if comp_res[0] != 0:
        return -1

    run_res = run_cmd(out_file, RUN_TIMEOUT)
    # pdb.set_trace()
    if ('runtime error:' in run_res[1]) or ('runtime error:' in run_res[2]):
        return -1

    comp_cmd = f'{CLANG} {comp_option} -w -O0 -fsanitize=undefined,address {src_file} -o {out_file}'
    comp_res = run_cmd(comp_cmd, SAN_COMPILE_TIMEOUT)
    # pdb.set_trace()
    if comp_res[0] != 0:
        return -1

    run_res = run_cmd(out_file, RUN_TIMEOUT)
    # pdb.set_trace()
    if ('runtime error:' in run_res[1]) or ('runtime error:' in run_res[2]):
        return -1


def generate(insert_plan, refine_list, org_file, new_file):
    line_cnt = 0
    new_prog = ''
    with open(org_file, 'r') as f:
        for line in f:
            line_cnt += 1
            var_refine_list = {}
            if line_cnt in refine_list.keys():
                if len(refine_list[line_cnt]) > 1:
                    for i in range(len(refine_list[line_cnt])):
                        if i == 0:
                            pos = refine_list[line_cnt][i]
                            var_feild = line[:pos - 1]
                            if '=' in var_feild:
                                var_refine_list[pos] = 1
                        else:
                            s_pos = refine_list[line_cnt][i - 1]
                            e_pos = refine_list[line_cnt][i]
                            var_feild = line[s_pos - 1:e_pos - 1]
                            if '=' in var_feild:
                                var_refine_list[e_pos] = s_pos + 1
            # if var_refine_list:
            # print(var_refine_list)
            if line_cnt in insert_plan.keys():
                insert_list = insert_plan[line_cnt]
                # print(insert_list)
                new_insert_list = []
                for insert_seq in insert_list:
                    if len(insert_seq) == 3:
                        if insert_seq[1] in var_refine_list.keys():
                            new_insert_list.append([var_refine_list[insert_seq[1]], insert_seq[-1]])
                        else:
                            new_insert_list.append([insert_seq[1], insert_seq[-1]])
                if not new_insert_list:
                    seq_list = insert_list
                else:
                    seq_list = new_insert_list
                sorted_insert_list = sorted(seq_list, key=lambda x: -x[0])
                # print(sorted_insert_list, '\n')
                new_line = line
                for insert_code in sorted_insert_list:
                    pos, code = insert_code
                    pos = pos - 1
                    new_line = new_line[:pos] + f' {code} ' + new_line[pos:]
                new_prog += new_line
            else:
                new_prog += line

    fw = open(new_file, 'w+')
    fw.write(new_prog)
    fw.close()


def generate_clang(insert_plan, refine_list, org_file, new_file):
    line_cnt = 0
    new_prog = ''
    with open(org_file, 'r') as f:
        for line in f:
            line_cnt += 1
            var_refine_list = {}
            if line_cnt in refine_list.keys():
                if len(refine_list[line_cnt]) > 1:
                    for i in range(len(refine_list[line_cnt])):
                        if i == 0:
                            pos = refine_list[line_cnt][i]
                            var_feild = line[:pos - 1]
                            if '=' in var_feild:
                                var_refine_list[pos] = 1
                        else:
                            s_pos = refine_list[line_cnt][i - 1]
                            e_pos = refine_list[line_cnt][i]
                            var_feild = line[s_pos - 1:e_pos - 1]
                            if '=' in var_feild:
                                var_refine_list[e_pos] = s_pos + 1

            if line_cnt in insert_plan.keys():
                insert_list = insert_plan[line_cnt]
                # print(insert_list)
                if len(insert_list) == 1 and insert_list[0][0] == 'loop':
                    insert_loop_code = f"{' ' * (insert_list[0][1] - 1)}{insert_list[0][-1]}\n"
                    new_prog += insert_loop_code
                    new_prog += line
                    continue
                new_insert_list = []
                for insert_seq in insert_list:
                    if len(insert_seq) == 3:
                        if insert_seq[1] in var_refine_list.keys():
                            new_insert_list.append([var_refine_list[insert_seq[1]], insert_seq[-1]])
                        else:
                            new_insert_list.append([insert_seq[1], insert_seq[-1]])
                if not new_insert_list:
                    seq_list = insert_list
                else:
                    seq_list = new_insert_list
                sorted_insert_list = sorted(seq_list, key=lambda x: -x[0])
                new_line = line
                for insert_code in sorted_insert_list:
                    pos, code = insert_code
                    pos = pos - 1
                    new_line = new_line[:pos] + f' {code} ' + new_line[pos:]
                new_prog += new_line
            else:
                new_prog += line

    fw = open(new_file, 'w+')
    fw.write(new_prog)
    fw.close()
