from dotenv import load_dotenv
from src.build_index import load_vec_db
from src.rag_complete import rag_complete
from trag_tree import build, hash
import time
import argparse

load_dotenv()

# example: python main.py --tree-num-max 50 --search-method 2
parser = argparse.ArgumentParser(description="Parse input arguments for RAG system.")
parser.add_argument('--vec-db-key', type=str, default="院志", help="The key for the vector database.")
parser.add_argument('--tree-num-max', type=int, default=50, help="The maximum number of trees to build.")
parser.add_argument('--entities-file-name', type=str, default="entities_file", help="The name of the entities file.")
parser.add_argument('--search-method', type=int, default=1, choices=[0, 1, 2, 4, 5, 6, 7], 
                    help="The search method to use: 0 for no tree, 1 for BFS, 2 for BloomFilter Search, 4 for simple hash, 5 for improved BloomFilter Search, 6 for improved BloomFilter-Cpp Search, 7 for Cuckoo filter.")
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

if search_method in [4]:
    for entity_tree in forest:
        entity_tree.bfs_hash()

if search_method in [7]:
    hash.cuckoo_build(tree_num_max, node_num_max)

stream = rag_complete(
    "瑞安市人民医院中有些什么？",
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

if search_method == 7:
    hash.cuckoo_sort()
    print("try to retrieve after sorting")
    stream = rag_complete(
        "瑞安市人民医院中有些什么？",
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
    