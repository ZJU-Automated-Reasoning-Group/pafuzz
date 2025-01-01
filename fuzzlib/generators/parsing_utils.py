import re
import subprocess
from .config import parse_tool, parse_tool_clang, PARSE_TIMEOUT

def parse_run_option(c_file):
    compile_map = {'preprocess': '-E', 'assemble': '-S', 'compile': '-c', 'link': '', 'run': '-o'}
    run_value, org_options_value = '', ''
    options_value = ''
    with open(c_file, 'r', encoding='ISO-8859-1') as fr:
        for line in fr:
            match_run = re.search(r'\bdo\s+(\w+)\s+\}', line)
            if match_run:
                run_value = match_run.group(1)

            match_options = re.search(r'options\s+"(.*?)"', line)
            if match_options:
                match_opt = match_options.group(1).strip()
                org_options_value = f'{org_options_value} {match_opt}'
    
    if '-O' in org_options_value:
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
