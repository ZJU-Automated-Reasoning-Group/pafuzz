import random
from . import optimizations

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
