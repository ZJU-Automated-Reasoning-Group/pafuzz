import os
import glob
import subprocess
import shutil

def find_c_files(directory, file_type):
    c_files = glob.glob(f'{directory}/**/*.{file_type}', recursive=True)
    return c_files

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

def merge_files(file1, file2, output_file):
    with open(output_file, 'w') as outfile:
        with open(file1, 'r') as infile1:
            outfile.write(infile1.read())
            outfile.write("\n")
        with open(file2, 'r') as infile2:
            outfile.write(infile2.read())

    os.remove(file1)
    os.remove(file2)

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

            if line_cnt in insert_plan.keys():
                insert_list = insert_plan[line_cnt]
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

    with open(new_file, 'w+') as fw:
        fw.write(new_prog)