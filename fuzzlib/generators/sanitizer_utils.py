import random
import subprocess
from . import attributes, sanitizers

def choose_gcc_sanitizer():
    select_sans = set()
    san_list = sanitizers.gcc_san
    random.shuffle(san_list)
    for san in san_list:
        if random.choice([0, 1]):
            select_sans.add(san)
    exsans = set()
    for san in select_sans:
        if san in exsans:
            continue
        if san in sanitizers.gcc_exclude_san.keys():
            esan = sanitizers.gcc_exclude_san[san]
            exsans = exsans | esan
    select_sans = select_sans - exsans
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

