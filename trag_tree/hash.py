import os
import sys

node_hash = dict()

current_dir = os.path.dirname(os.path.abspath(__file__))
so_path = os.path.join(current_dir, "..", "TRAG-cuckoofilter", "build")
sys.path.append(so_path)

import cuckoo_filter_module

filter = None


def change_filter(max_num_keys):
    global filter
    filter = cuckoo_filter_module.CuckooFilter(max_num_keys=max_num_keys)


def cuckoo_build(max_num, max_node):
    global filter
    filter.build(max_tree_num=max_num, max_node_num=max_node)


def cuckoo_extract(entity):
    global filter
    item_ = cuckoo_filter_module.EntityStruct()
    item_.content = entity
    info = filter.extract(item_)
    return info


def cuckoo_sort():
    global filter
    filter.sort()