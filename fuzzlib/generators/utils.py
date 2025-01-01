import subprocess
from . import config

def run_cmd(cmd, timeout, work_dir=None):
    if type(cmd) is not list:
        cmd = cmd.split(' ')
        cmd = list(filter(lambda x: x != '', cmd))
    
    if not work_dir:
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    else:
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=work_dir)
    
    try:
        output, error = process.communicate(timeout=timeout)
        output = output.decode('utf-8', errors='ignore')
        error = error.decode('utf-8', errors='ignore')
    except subprocess.TimeoutExpired:
        kill_all(process.pid)
        return 124, '', ''

    return process.returncode, output, error