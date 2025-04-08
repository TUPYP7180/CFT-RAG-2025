from dotenv import load_dotenv
from rag_base.build_index import load_vec_db
from rag_base.rag_complete import rag_complete
from trag_tree import build, hash
import time
import argparse
import csv
from ann.ann_calc import build_ann
from grag_graph.graph import build_graph

load_dotenv()

# example: python main.py --tree-num-max 50 --search-method 2
parser = argparse.ArgumentParser(description="Parse input arguments for RAG system.")
parser.add_argument('--vec-db-key', type=str, default="院志", help="The key for the vector database.")
parser.add_argument('--tree-num-max', type=int, default=50, help="The maximum number of trees to build.")
parser.add_argument('--entities-file-name', type=str, default="new_entities_file", help="The name of the entities file.")
parser.add_argument('--search-method', type=int, default=1, choices=[0, 1, 2, 5, 7, 8, 9], 
                    help="The search method to use: 0 for vec-db only, "
                    "1 for BFS, 2 for BloomFilter Search, 5 for improved BloomFilter Search,"
                    " 7 for Cuckoo filter, 8 for ANN-Tree, 9 for ANN-Graph")
parser.add_argument('--node-num-max', type=int, default=2000000, help="The maximum number of nodes to build.")

args = parser.parse_args()

vec_db_key = args.vec_db_key
tree_num_max = args.tree_num_max
entities_file_name = args.entities_file_name
search_method = args.search_method
node_num_max = args.node_num_max

start_time = time.time()

vec_db = load_vec_db(vec_db_key, "vec_db_cache/")
print("Load vector db finished")

forest, nlp = build.build_forest(tree_num_max, entities_file_name, search_method, node_num_max)
print("Load forest and nlp finished")

if search_method in [4, 8]:
    for entity_tree in forest:
        entity_tree.bfs_hash()

if search_method in [9]:
    build_graph(entities_file_name)

if search_method in [8, 9]:
    build_ann()

if search_method in [7]:
    hash.cuckoo_build(tree_num_max, node_num_max)

entities_list = set()
with open(entities_file_name+".csv", "r", encoding='utf-8') as csvfile:
    csvreader = csv.reader(csvfile, delimiter=',')
    for row in csvreader:
        if len(row) >= 2:
            entities_list.add(row[0].strip())
            entities_list.add(row[1].strip())

# query = '请介绍这些名词：'+ ' '.join(list(entities_list)[:20])
query = 'question: who are you?'

print(query)

stream = rag_complete(
    query,
    vec_db,
    forest,
    nlp,
    search_method=search_method,
    debug=True,
)

start = True
for chunk in stream:
    if start:
        print("==== Result ====")
        start = False
    print(chunk, end="")
print()

end_time = time.time()
execution_time = end_time - start_time
print(f"\033[1;31mExecution Time: {execution_time:.6f} seconds\033[0m")
