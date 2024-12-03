import datetime
import logging
import multiprocessing
import os
import random
import re
import shutil
import string
import tempfile

from fuzzlib.generators.utils import parse_ast_clang, generate_clang, \
    parse_run_option, filter_opt, run_cmd, filter_crash, find_c_files

current_time = datetime.datetime.now()
timestamp = current_time.strftime("%Y%m%d_%H%M%S")
CUR_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), f'0-ATTRIBUTE-{timestamp}')
CRASH_DIR = os.path.join(CUR_DIR, 'crash')
BUG_DIR = os.path.join(CUR_DIR, 'bug')

COMPILATION_TIMEOUT = 10
RUN_TIMEOUT = 30
CSMITH_HOME = '/home/compiler/csmith/runtime'

CLANG = 'clang'
GCC = 'gcc'
TEST_SUITE_DIR = '/home/compiler/gcc/gcc/testsuite'
# TEST_SUITE_DIR = '/home/compiler/llvm-test-suite'

GCC_CRASH_INFO = 'please submit a full bug report'
CLANG_CRASH_INFO = 'please submit a bug report to'

bug1 = 'fatal error: error in backend: segmented stacks do not support vararg functions.'
bug2 = 'fatal error: error in backend: stack realignment in presence of dynamic allocas is not supported withthis calling convention.'
bug3 = 'fatal error: error in backend: access past stack top!'
bug4 = 'fatal error: error in backend: zmm registers are not supported without evex512'
bug5 = 'Debug Variable Analysis'
bug6 = 'X86 FP Stackifier'

struct_attributes = [
    '__single_inheritance',
    '__multiple_inheritance',
    '__virtual_inheritance',
    '__unspecified_inheritance',
    '__attribute__((deprecated))',
    '__attribute__((lto_visibility_public))',
    '__attribute__((randomize_layout))',
    '__attribute__((no_randomize_layout))',
    '__attribute__((enforce_read_only_placement))',
]

enum_attributes = [
    'enum_extensibility',
    '__attribute__((flag_enum))',

]

union_attributes = [
    '__attribute__((transparent_union))',
    # '__declspec(empty_bases)',
]

struct_related_attributes = [
    'btf_decl_tag',
    'aligned',
    '__attribute__((packed))',
    'vector_size'
]

variable_related_attributes = [
    'asm',
    '__attribute__((deprecated))',
    '__attribute__((weak))',
    'omp_target',
    # '_Nonnull',
    # '_Null_unspecified',
    # '_Nullable',
    # '_Nullable_result',
    '__attribute__((opencl_global_device))',
    '__attribute__((opencl_global_host))',
    '__attribute__((opencl_generic))',
    '__attribute__((opencl_global))',
    '__attribute__((opencl_local))',
    '__attribute__((opencl_private))',
    'align_value',
    'noderef',
    'aligned',
    '__attribute__((common))',
    'mode',
    '__attribute__((nocommon))',
    'visibility',
    'release_handle',
]

function_related_attributes = [
    '__attribute__((fastcall))',
    '__attribute__((preserve_all))',
    '__attribute__((preserve_most))',
    '__attribute__((preserve_none))',
    '__attribute__((regcall))',
    '__attribute__((riscv_vector_cc))',
    '__attribute__((vectorcall))',
    'callable_when',
    '__attribute__((param_typestate))',
    # 'asm',
    '__attribute__((deprecated))',
    '__attribute__((weak))',
    'func_simd',
    'omp_target',
    # '#pragma omp declare variant',
    '_Noreturn',
    'abi_tag',
    '__attribute__((acquire_capability))',
    '__attribute__((acquire_shared_capability))',
    '__attribute__((exclusive_lock_function))',
    '__attribute__((shared_lock_function))',
    'alloc_size',
    'alloc_align',
    # '__declspec(allocator)',
    '__attribute__((always_inline))',
    '__attribute__((artificial))',
    '__attribute__((assert_capability))',
    '__attribute__((assert_shared_capability))',
    'assume_aligned',
    'callback',
    'btf_decl_tag',
    '__attribute__((cold))',
    '__attribute__((constructor))',
    '__attribute__((convergent))',
    'cpu_dispatch',
    'cpu_specific',
    '__attribute__((destructor))',
    '__attribute__((disable_tail_calls))',
    'enforce_tcb',
    'enforce_tcb_leaf',
    'warning',
    '__attribute__((flatten))',
    '__attribute__((force_align_arg_pointer))',
    '__attribute__((gnu_inline))',
    '__attribute__((hot))',
    # 'ifunc',
    'malloc',
    'min_vector_width',
    '__attribute__((minsize))',
    '__attribute__((no_builtin))',
    '__attribute__((no_caller_saved_registers))',
    '__attribute__((no_speculative_load_hardening))',
    '__attribute__((speculative_load_hardening))',
    # '__declspec(noalias)',
    # '__attribute__((noconvergent))',
    '__attribute__((warn_unused_result))',
    '__attribute__((noduplicate))',
    '__attribute__((noinline))',
    'noreturn',
    '__attribute__((nothrow))',
    '__attribute__((nouwtable))',
    '__attribute__((optnone))',
    'patchable_function_entry',
    '__attribute__((release_capability))',
    '__attribute__((release_shared_capability))',
    '__attribute__((release_generic_capability))',
    '__attribute__((unlock_function))',
    '__attribute__((retain))',
    'target',
    'target_clones',
    'try_acquire_capability',
    'try_acquire_shared_capability',
    '__attribute__((unsafe_buffer_usage))',
    '__attribute__((used))',
    '__attribute__((xray_always_instrument))',
    '__attribute__((xray_never_instrument))',
    '__attribute__((xray_log_args(1)))',
    'zero_call_used_regs',
    'acquire_handle',
    'use_handle',
    'nonnull',
    'returns_nonnull',
    '__attribute__((opencl_global_device))',
    '__attribute__((opencl_global_host))',
    '__attribute__((opencl_constant))',
    '__attribute__((opencl_generic))',
    '__attribute__((opencl_global))',
    '__attribute__((opencl_local))',
    '__attribute__((opencl_private))',
    '__attribute__((allocating))',
    '__attribute__((blocking))',
    '__attribute__((nonallocating))',
    '__attribute__((nonblocking))',
    '__attribute__((nomerge))',
    'aligned',
    '__attribute__((const))',
    '__attribute__((pure))',
    '__attribute__((returns_twice))',
    'sentinel',
    'vector_size_func',
    'visibility',
    '__attribute__((weakref))',
    '__attribute__((called_once))',
    '__attribute__((unused))',
    # '__declspec(empty_bases)',
    # '__attribute__(())',

]

loop_related_attributes = [
    '#pragma omp simd',
    'clang_loop',
    '#pragma unroll',
    '#pragma nounroll',
    '#pragma unroll_and_jam',
    '#pragma unroll_and_jam',
    '#pragma unroll_and_jam',
    # '__attribute__((fallthrough))',
    '__attribute__((opencl_unroll_hint))',
    'code_align'
]

function_related_attributes_option = {
    '__attribute__((disable_sanitizer_instrumentation))': ['-fsanitize=address', '-fsanitize=thread',
                                                           '-fsanitize=memory', '-fsanitize=undefined',
                                                           '-fsanitize=dataflow'],
    '__attribute__((no_profile_instrument_function))': ['-fprofile-generate', '-fprofile-instr-generate',
                                                        '-fcs-profile-generate', '-fprofile-arcs'],
    # 'no_sanitize': [],
    '__attribute__((no_sanitize_address))': '-fsanitize=address',
    '__attribute__((no_address_safety_analysis))': '-fsanitize=address',
    '__attribute__((no_sanitize_thread))': '-fsanitize=thread',
    '__attribute__((no_sanitize_memory))': '-fsanitize=memory',
    '__attribute__((no_split_stack))': '-fsplit-stack',
    '__attribute__((no_stack_protector))': '-fstack-protector',
    '__attribute__((nocf_check))': '-fcf-protection',
    # '__declspec(noalias)': ['-fdeclspec', '-fms-extensions'],
    # '__declspec((strict_gs_check))': ['-fdeclspec', '-fms-extensions'],
    '__attribute__((no_instrument_function))': '-finstrument-functions',
    '__attribute__((nodebug))': '-g'
}


def form_callable_when(info):
    consumed_type_list = ['unconsumed', 'consumed', 'unknown']
    consumed_type = random.choice(consumed_type_list)
    return f'__attribute__ ((callable_when("{consumed_type}")))'


def form_asm(info):
    all_characters = string.ascii_letters + string.digits
    random_string = ''.join(random.choice(all_characters) for i in range(random.randint(3, 10)))
    return f'asm("{random_string}")'


def form_enum_extensibility(info):
    type_list = ['open', 'closed']
    t = random.choice(type_list)
    return f'__attribute__ ((callable_when("{t}")))'


def form_declare_smid(info):
    para_list = info[-1]
    clauses_type_lists = ['simdlen', 'linear', 'aligned', 'uniform', 'inbranch', 'notinbranch', '']
    clauses_type = random.choice(clauses_type_lists)
    if clauses_type == 'inbranch':
        return f'#pragma omp declare simd {clauses_type}'
    if clauses_type == 'notinbranch':
        return f'#pragma omp declare simd {clauses_type}'
    if clauses_type == 'simdlen':
        simdlen = random.randint(1, 8)
        return f'#pragma omp declare simd simdlen({simdlen})'
    if clauses_type == 'linear':
        return f'#pragma omp declare simd linear()'
    if clauses_type == 'uniform':
        return f'#pragma omp declare simd uniform()'
    if clauses_type == 'aligned':
        return f'#pragma omp declare simd aligned()'
    if clauses_type == '':
        return f'#pragma omp declare simd'


def form_omp_target(info):
    pass


def insert_noreturn(info):
    func_ret_type = info[1]
    if func_ret_type == 'void':
        return '_Noreturn'


def form_abi_tag(info):
    # all_characters = string.ascii_letters + string.digits + string.punctuation
    all_characters = string.ascii_letters + string.digits
    random_string = ''.join(random.choice(all_characters) for i in range(random.randint(3, 10)))
    return f'__attribute__((abi_tag("{random_string}")))'


def form_callback(info):
    pass


def form_btf_decl_tag(info):
    all_characters = string.ascii_letters + string.digits
    random_string = ''.join(random.choice(all_characters) for i in range(random.randint(3, 10)))
    return f'__attribute__((btf_decl_tag("{random_string}")))'


def form_cpu_dispatch(info):
    cpu_type_list = ['ivybridge', 'atom', 'sandybridge']
    cpu_type = random.choice(cpu_type_list)
    return f'__attribute__ ((cpu_dispatch({cpu_type})))'


def form_cpu_specific(info):
    cpu_type_list = ['ivybridge', 'atom', 'sandybridge']
    cpu_type = random.choice(cpu_type_list)
    return f'__attribute__((cpu_specific({cpu_type})))'


def form_warning(info):
    all_characters = string.ascii_letters + string.digits
    random_string = ''.join(random.choice(all_characters) for i in range(random.randint(3, 10)))
    return f'__attribute__((warning("{random_string}")))'


def form_ifunc(info):
    pass


def form_malloc(info):
    func_ret_type = info[1]
    if "*" in func_ret_type:
        return '__attribute__((malloc))'


def form_min_vector_width(info):
    width_list = [16, 32, 64, 128, 256, 521]
    width = random.choice(width_list)
    return f'__attribute__((min_vector_width({width})))'


def form_noreturn(info):
    func_ret_type = info[1]
    if func_ret_type == 'void':
        return '__attribute__((noreturn))'


def form_patchable_function_entry(info):
    n_list = [4, 8, 16, 32, 64, 128]
    n = random.choice(n_list)
    m = random.randint(0, 4)
    return f'__attribute__((patchable_function_entry({n}, {m})))'


def form_try_acquire_capability(info):
    boolean = random.randint(0, 1)
    return f'__attribute__((try_acquire_capability({boolean})))'


def form_try_acquire_shared_capability(info):
    boolean_list = ['true', 'false']
    boolean = random.choice(boolean_list)
    return f'__attribute__((try_acquire_shared_capability({boolean})))'


def form_acquire_handle(info):
    all_characters = string.ascii_letters + string.digits
    random_string = ''.join(random.choice(all_characters) for i in range(random.randint(3, 10)))
    return f'__attribute__((acquire_handle("{random_string}")))'


def form_release_handle(info):
    all_characters = string.ascii_letters + string.digits
    random_string = ''.join(random.choice(all_characters) for i in range(random.randint(3, 10)))
    return f'__attribute__((release_handle("{random_string}")))'


def form_use_handle(info):
    all_characters = string.ascii_letters + string.digits
    random_string = ''.join(random.choice(all_characters) for i in range(random.randint(3, 10)))
    return f'__attribute__((use_handle("{random_string}")))'


def insert_noderef(info):
    var_type = info[1]
    if '*' in var_type:
        return '__attribute__((noderef))'


def form_align_value(info):
    var_type = info[1]
    if '*' in var_type:
        num_candidate = ['4', '8', '16', '32', '64', '128']
        num = random.choice(num_candidate)
        return f'__attribute__((align_value({num})))'


def form_code_align(info):
    num_candidate = ['4', '8', '16', '32', '64', '128']
    num = random.choice(num_candidate)
    return f'__attribute__((code_align({num})))'


def form_aligned(info):
    num_candidate = ['4', '8', '16', '32', '64']
    num = random.choice(num_candidate)
    return f'__attribute__((aligned({num})))'


def form_alloc_size(info):
    func_ret_type, para_list = info[1], info[-1]
    if 'size_t' not in para_list:
        return
    para_list = para_list.strip('()').split(',')
    if '*' not in func_ret_type:
        return
    if len(para_list) == 0:
        return
    size_t_pos = [index + 1 for index, item in enumerate(para_list) if item == 'size_t']
    if len(size_t_pos) == 1:
        return f'__attribute__((alloc_size({size_t_pos[0]}))'
    two_pos = random.sample(size_t_pos, 2)
    return f'__attribute__((alloc_size({two_pos[0]}, {two_pos[1]}))'


def insert_nonstring(info):
    var_type = info[1]
    var_type = var_type.replace(' ', '')
    if 'char[' in var_type:
        return '__attribute__((nonstring))'


def form_mode(info):
    var_type = info[1]
    if '*' in var_type:
        mode_type = ['byte', '__byte__', 'word', '__word__', 'pointer', '__pointer__']
        mode = random.choice(mode_type)
        return f'__attribute__((mode({mode})))'
    else:
        mode_type = ['byte', '__byte__', 'word', '__word__']
        mode = random.choice(mode_type)
        return f'__attribute__((mode({mode})))'


def form_strict_flex_array(info):
    var_type = info[1]
    if not re.search(r"\[.*?\]", var_type):
        return
    level_list = [0, 1, 2, 3]
    level = random.choice(level_list)
    return f'__attribute__((strict_flex_array({level})))'


def insert_tls_model(info):
    var_type = info[1]
    if var_type == '__thread':
        return '__attribute__((tls_model("tls_model")))'


def form_vector_size(info):
    num_candidate = ['4', '8', '16', '32', '64']
    num = random.choice(num_candidate)
    return f'__attribute__((vector_size({num})))'


def form_vector_size_func(info):
    func_ret_type = info[1].strip()
    if func_ret_type != 'void':
        num_candidate = ['4', '8', '16', '32', '64']
        num = random.choice(num_candidate)
        return f'__attribute__((vector_size({num})))'


def form_warn_if_not_aligned(info):
    num_candidate = ['4', '8', '16', '32', '64', '__BIGGEST_ALIGNMENT__']
    num = random.choice(num_candidate)
    return f'__attribute__((warn_if_not_aligned({num})))'


def form_visibility(info):
    visibility_type_list = ['default', 'hidden', 'internal', 'protected']
    visibility_type = random.choice(visibility_type_list)
    return f'__attribute__ ((visibility("{visibility_type}")))'


def form_access(info):
    para_list = info[-1]
    if '*' not in para_list:
        return
    mode_list = ['read_only', 'write_only', 'read_write']
    para_list = para_list.strip('()').split(',')
    size_t_pos = [index + 1 for index, item in enumerate(para_list) if item == 'size_t']
    pointer_pos = [index + 1 for index, item in enumerate(para_list) if '*' in item]
    if len(size_t_pos) == 0:
        if len(pointer_pos) == 1:
            mode = random.choice(mode_list)
            return f'__attribute__((access({mode}, {pointer_pos[0]})))'
        else:
            para_pos = random.choice(pointer_pos)
            mode = random.choice(mode_list)
            return f'__attribute__((access({mode}, {para_pos})))'
    else:
        size_t = random.choice(size_t_pos)
        if len(pointer_pos) == 1:
            mode = random.choice(mode_list)
            return f'__attribute__((access({mode}, {pointer_pos[0]}, {size_t})))'
        else:
            para_pos = random.choice(pointer_pos)
            mode = random.choice(mode_list)
            return f'__attribute__((access({mode}, {para_pos}, {size_t})))'


def form_alloc_align(info):
    func_ret_type, para_list = info[1], info[-1]
    if 'size_t' not in para_list:
        return
    para_list = para_list.strip('()').split(',')
    if '*' not in func_ret_type:
        return
    if len(para_list) == 0:
        return
    size_t_pos = [index + 1 for index, item in enumerate(para_list) if item == 'size_t']
    size_t = random.choice(size_t_pos)
    return f'__attribute__((alloc_align({size_t}))'


def form_assume_aligned(info):
    func_ret_type = info[1]
    if '*' not in func_ret_type:
        return
    num_candidate = ['4', '8', '16', '32', '64']
    num = random.choice(num_candidate)
    if num == '1':
        return f'__attribute__((assume_aligned({num})))'
    else:
        offset_use = random.randint(0, 1)
        if offset_use:
            return f'__attribute__((assume_aligned({num}, {random.randint(1, int(num) - 1)})))'
        else:
            return f'__attribute__((assume_aligned({num})))'


def form_nonnull(info):
    para_list = info[-1]
    if '*' not in para_list:
        return
    para_list = para_list.strip('()').split(',')
    pointer_pos = [index + 1 for index, item in enumerate(para_list) if '*' in item]
    if len(pointer_pos) == 1:
        return f'__attribute__((nonnull({pointer_pos[0]})))'
    else:
        chose_pointer_list = random.sample(pointer_pos, random.randint(2, len(pointer_pos)))
        ppos = ','.join(map(str, chose_pointer_list))
        return f'__attribute__((nonnull({ppos})))'


def form_null_terminated_string_arg(info):
    para_list = info[-1]
    para_list = para_list.strip('()').split(',')
    para_list = [_.replace(' ', '') for _ in para_list]
    char_para_pos = [index + 1 for index, item in enumerate(para_list) if 'char*' in item]
    if len(char_para_pos) == 0:
        return
    else:
        pos = random.choice(char_para_pos)
        return f'__attribute__((null_terminated_string_arg({pos})))'


def form_returns_nonnull(info):
    func_ret_type = info[1]
    if '*' in func_ret_type:
        return '__attribute__((returns_nonnull))'


def form_sentinel(para_list):
    if '...' in para_list:
        return '__attribute__((sentinel))'


def form_target(info):
    isa_list = [
        'sse', 'sse2', 'sse3', 'sse4.1', 'sse4.2', 'sse4a',
        'avx', 'avx2', 'avx512f', 'avx512cd', 'avx512er', 'avx512pf', 'avx512vl', 'avx512bw', 'avx512dq',
        'mmx', 'popcnt', 'bmi', 'bmi2', 'fma', 'xop'
    ]
    isa = random.choice(isa_list)
    return f'__attribute__((target("{isa}")))'


def form_target_clones(info):
    isa_list = [
        'sse', 'sse2', 'sse3', 'sse4.1', 'sse4.2', 'sse4a',
        'avx', 'avx2', 'avx512f', 'avx512cd', 'avx512er', 'avx512pf', 'avx512vl', 'avx512bw', 'avx512dq',
        'mmx', 'popcnt', 'bmi', 'bmi2', 'fma', 'xop'
    ]
    isas = random.sample(isa_list, 4)
    isas = [f'"{_}"' for _ in isas]
    form_isa = ','.join(map(str, isas))
    return f'__attribute__((target_clones({form_isa})))'


def form_zero_call_used_regs(info):
    choice_list = ['skip', 'used', 'used-gpr', 'used-arg', 'used-gpr-arg', 'all', 'all-gpr',
                   'all-arg', 'all-gpr-arg', 'leafy', 'leafy-gpr', 'leafy-arg', 'leafy-gpr-arg']
    choice = random.choice(choice_list)
    return f'__attribute__((zero_call_used_regs("{choice}")))'


def form_clang_loop(info):
    loop_option_list = ['unroll(enable)', 'unroll(disable)', 'vectorize(enable)', 'vectorize(disable)',
                        'interleave(enable)', 'interleave(disable)', 'distribute(enable)', 'distribute(disable)']
    loop_option = random.choice(loop_option_list)
    return f'#pragma clang loop {loop_option}'


def form_enforce_tcb(info):
    all_characters = string.ascii_letters + string.digits
    random_string = ''.join(random.choice(all_characters) for i in range(random.randint(3, 10)))
    return f'__attribute__((enforce_tcb("{random_string}")))'


def form_enforce_tcb_leaf(info):
    all_characters = string.ascii_letters + string.digits
    random_string = ''.join(random.choice(all_characters) for i in range(random.randint(3, 10)))
    return f'__attribute__((enforce_tcb_leaf("{random_string}")))'


attribute_function_map = {
    'callable_when': form_callable_when,
    'asm': form_asm,
    'enum_extensibility': form_enum_extensibility,
    'func_simd': form_declare_smid,
    'omp_target': form_omp_target,
    'abi_tag': form_abi_tag,
    '_Noreturn': insert_noreturn,
    'noreturn': insert_noreturn,
    'alloc_size': form_alloc_size,
    'alloc_align': form_alloc_align,
    'assume_aligned': form_assume_aligned,
    'btf_decl_tag': form_btf_decl_tag,
    'cpu_dispatch': form_cpu_dispatch,
    'cpu_specific': form_cpu_specific,
    'warning': form_warning,
    'ifunc': form_ifunc,
    'malloc': form_malloc,
    'min_vector_width': form_min_vector_width,
    'patchable_function_entry': form_patchable_function_entry,
    'target': form_target,
    'target_clones': form_target_clones,
    'try_acquire_capability': form_try_acquire_capability,
    'try_acquire_shared_capability': form_try_acquire_shared_capability,
    'zero_call_used_regs': form_zero_call_used_regs,
    'acquire_handle': form_acquire_handle,
    'release_handle': form_release_handle,
    'use_handle': form_use_handle,
    'nonnull': form_nonnull,
    'returns_nonnull': form_returns_nonnull,
    'align_value': form_align_value,
    'noderef': insert_noderef,
    'aligned': form_aligned,
    'mode': form_mode,
    'sentinel': form_sentinel,
    'vector_size': form_vector_size,
    'code_align': form_code_align,
    'vector_size_func': form_vector_size_func,
    'visibility': form_visibility,
    'clang_loop': form_clang_loop,
    'enforce_tcb': form_enforce_tcb,
    'enforce_tcb_leaf': form_enforce_tcb_leaf,
}


def get_logger(log_dir, name):
    if not os.path.exists(CUR_DIR):
        os.mkdir(CUR_DIR)

    logger = logging.getLogger(name)
    filename = f'{log_dir}/{name}.log'
    fh = logging.FileHandler(filename, mode='w+', encoding='utf-8')
    formatter = logging.Formatter('%(levelname)s:\n%(message)s')
    logger.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    return logger


bug_logger = get_logger(CUR_DIR, 'BUG')
record_logger = get_logger(CUR_DIR, 'RECORD')
err_logger = get_logger(CUR_DIR, 'ERR')
info_logger = get_logger(CUR_DIR, 'INFO')


class RunTest(object):

    def __init__(self, prog, pre, opt, org_opt, link_dir, work_dir):
        self.prog = prog
        self.pre = pre
        self.opt = opt
        self.org_opt = org_opt
        self.link_dir = link_dir
        self.work_dir = work_dir

        self.strut_var_list = []
        self.var_list = []
        self.func_list = []
        self.loop_list = []
        self.struct_list = []
        self.refine_list = {}

        self.case_list = {}

    def pre_run(self, comp):
        pre_comp = self.get_oracle(comp, f'{self.org_opt} -c', self.prog)
        info_logger.info(f'[Pre Compilation Done]:{self.prog}')
        # print(pre_comp)
        if pre_comp[0] != 0:
            return -1

        parse_options = f'-I{self.link_dir} {self.org_opt}'
        ret_info = parse_ast_clang(self.prog, parse_options, self.work_dir)
        if not ret_info:
            return -1
        [self.strut_var_list, self.var_list, self.func_list, self.loop_list, self.struct_list,
         self.refine_list] = ret_info

    def form_insert_plan(self):
        insert_plan = {}
        for struct_var in self.strut_var_list:
            inserted = random.randint(0, 9)
            if inserted < 3:
                continue
            chose_attributes = random.choice(struct_related_attributes)
            attribute_code = chose_attributes
            if chose_attributes in attribute_function_map.keys():
                form_function = attribute_function_map[chose_attributes]
                attribute_code = form_function(struct_var)
                if not attribute_code:
                    continue
            if int(struct_var[3]) not in insert_plan.keys():
                insert_plan[int(struct_var[3])] = [[int(struct_var[-2]), attribute_code]]
            else:
                insert_plan[int(struct_var[3])].append([int(struct_var[-2]), attribute_code])

        for struct in self.struct_list:
            inserted = random.randint(0, 9)
            if inserted < 2:
                continue
            chose_attributes = random.choice(struct_attributes)
            attribute_code = chose_attributes
            if chose_attributes in attribute_function_map.keys():
                form_function = attribute_function_map[chose_attributes]
                attribute_code = form_function(struct)
                if not attribute_code:
                    continue
            # [endline: [endcolumn, code]]
            if int(struct[-2]) not in insert_plan.keys():
                insert_plan[int(struct[-2])] = [[int(struct[-1]), attribute_code]]
            else:
                insert_plan[int(struct[-2])].append([int(struct[-1]), attribute_code])

        for var in self.var_list:
            if 'Local' in var[2]:
                continue
            if var[-1] == '0' and var[-2] == '0' and var[-3] == '0':
                continue
            inserted = random.randint(0, 9)
            if inserted < 4:
                continue
            chose_attributes = random.choice(variable_related_attributes)
            attribute_code = ''
            if chose_attributes in attribute_function_map.keys():
                form_function = attribute_function_map[chose_attributes]
                attribute_code = form_function(var)
                if not attribute_code:
                    continue
            if int(var[3]) not in insert_plan.keys():
                insert_plan[int(var[3])] = [[int(var[-2]), int(var[-1]), attribute_code]]
            else:
                insert_plan[int(var[3])].append([int(var[-2]), int(var[-1]), attribute_code])

        option_list = set()
        san_flag = False
        for func in self.func_list:
            inserted = random.randint(0, 9)
            if inserted < 4:
                continue
            chose_attributes = random.choice(function_related_attributes)
            attribute_code = chose_attributes
            if chose_attributes in attribute_function_map.keys():
                form_function = attribute_function_map[chose_attributes]
                attribute_code = form_function(func)
                if not attribute_code:
                    continue
            # [line: [column, code]]
            if 'abi_tag' not in chose_attributes:
                other_attribute = random.choice(list(function_related_attributes_option.keys()))
                options = function_related_attributes_option[other_attribute]
                if not isinstance(options, str):
                    options = random.choice(options)
                if '-fsanitiz=' in options:
                    if not san_flag:
                        san_flag = True
                        option_list.add(options)
                else:
                    option_list.add(options)
                attribute_code += f' {other_attribute}'
            if int(func[2]) not in insert_plan.keys():
                insert_plan[int(func[2])] = [[int(func[3]), attribute_code]]
            else:
                insert_plan[int(func[2])].append([int(func[3]), attribute_code])

        for loop in self.loop_list:
            inserted = random.randint(0, 9)
            if inserted < 5:
                continue
            chose_attributes = random.choice(loop_related_attributes)
            attribute_code = chose_attributes
            if chose_attributes in attribute_function_map.keys():
                form_loop = attribute_function_map[chose_attributes]
                attribute_code = form_loop(loop)
                if not attribute_code:
                    continue
            # [line: [column, code]]
            insert_plan[int(loop[0])] = [['loop', int(loop[1]), attribute_code]]

        return insert_plan, option_list

    def insert_attribute(self):
        base_name = os.path.basename(self.prog)
        insert_nums = 80
        for index in range(insert_nums):
            file_name, ext = os.path.splitext(base_name)
            new_base_name = f'{file_name}+insert{index}{ext}'
            new_test_case = f'{self.work_dir}/{new_base_name}'
            insert_plan, option_list = self.form_insert_plan()
            if not insert_plan:
                continue
            generate_clang(insert_plan, self.refine_list, self.prog, new_test_case)
            options = ' '.join(list(option_list))
            # pdb.set_trace()
            self.case_list[new_test_case] = options

    def get_oracle(self, compiler, option, prog):
        if 'gcc' in compiler:
            CRASH_INFO = GCC_CRASH_INFO
        if 'clang' in compiler:
            CRASH_INFO = CLANG_CRASH_INFO
        # compile
        if self.pre != '-o':
            compile_cmd = f'{compiler} -I{self.link_dir} {option} {prog} {self.pre}'
        else:
            out_file = f'{self.work_dir}/{os.path.basename(prog)}'
            base_name, ext = os.path.splitext(out_file)
            out_file = base_name + '.out'
            compile_cmd = f'{compiler} -I{self.link_dir} {option} {prog} -o {out_file}'
        compile_ret_code, compile_ret, compile_error = run_cmd(compile_cmd, COMPILATION_TIMEOUT, self.work_dir)
        if compile_ret_code != 0:
            if CRASH_INFO in compile_error.lower() and 'c/c-decl.cc:9689' not in compile_error.lower() and 'c/c-typeck.cc:1178' not in compile_error.lower() and bug1 not in compile_error.lower() and bug2 not in compile_error.lower() and bug3 not in compile_error.lower() and bug4 not in compile_error.lower() and bug5.lower() not in compile_error.lower() and bug6.lower() not in compile_error.lower():
                if 'gcc' in compiler:
                    compile_error = filter_crash(compile_error, 'internal compiler error:')
                bug_logger.critical(
                    f"[Compiler]: {compiler}\n[Prog]: {prog}\n[Reference]: {compile_cmd}\n[Error Code]: {compile_ret_code}\n[Error Message]: {compile_error}\n")
                if not os.path.exists(f'{CRASH_DIR}/{os.path.basename(prog)}'):
                    shutil.copy(prog, CRASH_DIR)
                return compile_ret_code, '', ''
            if (compile_ret_code == 139) or (compile_ret_code == 134):
                bug_logger.critical(
                    f"[Compiler]: {compiler}\n[Prog]: {prog}\n[Reference]: {compile_cmd}\n[Error Code]: {compile_ret_code}\n[Error Message]: {compile_error}\n")
                if not os.path.exists(f'{CRASH_DIR}/{os.path.basename(prog)}'):
                    shutil.copy(prog, CRASH_DIR)
                return compile_ret_code, '', ''
            return compile_ret_code, '', ''

        return compile_ret_code, '', ''

        if self.pre != '-o':
            return (compile_ret_code, '', '')

        if not os.path.exists(out_file):
            return compile_ret_code, '', ''

        run_file_cmd = f'{out_file}'
        run_ret_code, run_ret, run_error = utils.run_cmd(run_file_cmd, RUN_TIMEOUT, self.work_dir)
        if run_ret_code != 0:
            err_logger.error(
                f'[Prog]:{prog}\n[run_ret_code]:{run_ret_code}\n[run_ret]:{run_ret}\n[run_error]:{run_error}\n')
        if 'runtime error:' in run_error and not run_ret:
            run_ret = 'runtime error'
        return (compile_ret_code, run_ret_code, run_ret)

    def get_res(self, compiler):
        for prog, comp_o in self.case_list.items():
            for o in ['-O0', '-O1', '-O2', '-O3', '-Os', '-Ofast']:
                for func_opt in ['', '-g', '-flto']:
                    comp_option = f'{o} {func_opt} {self.opt} {comp_o}'
                    oracle = self.get_oracle(compiler, comp_option, prog)
                    # pdb.set_trace()
        # info_logger.info(f'[Compilation Done]\n[Prog]:{self.prog}\n')


c_test_cases = find_c_files(TEST_SUITE_DIR, 'c')

processed_cases = []

skip_files = [

]

remains = list(set(c_test_cases) - set(processed_cases))


def run(i):
    test_case = remains[i]
    if test_case in skip_files:
        return
    pre, opt, org_opt = parse_run_option(test_case)
    print(test_case, flush=True)
    record_logger.info(f'[Processing]: [Prog]:{test_case}\n')

    with tempfile.TemporaryDirectory() as work_dir:
        run_test = RunTest(test_case, '-c', filter_opt(opt), org_opt, os.path.dirname(test_case), work_dir)
        pre_res = run_test.pre_run(CLANG)
        if pre_res == -1:
            err_logger.error(f'[Parse Error]: {run_test.prog}\n')
            return
        run_test.insert_attribute()
        run_test.get_res(CLANG)

        info_logger.info(f'[Compilation Done]\n[Prog]:{run_test.prog}\n')


if __name__ == '__main__':
    if not os.path.exists(BUG_DIR):
        os.mkdir(BUG_DIR)

    if not os.path.exists(CRASH_DIR):
        os.mkdir(CRASH_DIR)

    print(f'[Total prog]: {len(c_test_cases)}', flush=True)
    print(f'[Remains]: {len(remains)}', flush=True)

    # for i in range(len(remains)):
    #     run(i)
    proc_num = 46
    pool = multiprocessing.Pool(proc_num)

    pool.map(run, range(len(remains)))

    pool.close()
    pool.join()
