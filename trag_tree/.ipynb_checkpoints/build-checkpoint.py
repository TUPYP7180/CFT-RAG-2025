# -*- encoding:utf-8 -*-

from entity import ruler
from trag_tree import EntityTree
import csv
import pickle
import os


def get_dump_file_path(tree_num_max, entities_file_name):
    return f"./entity_forest_cache/forest_nlp_entities_file_{entities_file_name}_tree_num_{tree_num_max}.pkl"
    

def build_forest(tree_num_max=30, entities_file_name="entities_file"):

    dump_file_path = get_dump_file_path(tree_num_max, entities_file_name)

    if os.path.exists(dump_file_path):
        print(f"Loading cached forest and nlp from {dump_file_path}...")
        with open(dump_file_path, 'rb') as f:
            forest, nlp = pickle.load(f)
        return forest, nlp
    
    rel = []
    entities_list = set()
    with open(entities_file_name+".csv", "r", encoding='utf-8') as csvfile:
        csvreader = csv.reader(csvfile, delimiter=',')
        for row in csvreader:
            if len(row) >= 2:
                rel.append({'subject': row[0].strip(), 'object': row[1].strip()})
                entities_list.add(row[0].strip())
                entities_list.add(row[1].strip())

    nlp = ruler.enhance_spacy(list(entities_list))

    data = []
    root_list = set()
    out_degree = set()
    forest = []

    for dependency in rel:
        data.append([dependency['subject'].lower().strip(), dependency['object'].lower().strip()])
        out_degree.add(dependency['subject'].lower().strip())

    for edge in data:
        if edge[1] not in out_degree:
            root_list.add(edge[1])

    success_num = 0
    for root in root_list:
        # print("build tree...")
        new_tree = EntityTree(root, data)
        forest.append(new_tree)
        success_num += 1
        if success_num > tree_num_max:
            break

    with open(dump_file_path, 'wb') as f:
        pickle.dump((forest, nlp), f)

    return forest, nlp
