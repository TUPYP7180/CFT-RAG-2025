from trag_tree import build, hash
import time
import csv
from entity import ruler

tree_num_max = 100
entities_file_name = 'entities_file'
node_num_max = 2000000

forest, nlp = build.build_forest(tree_num_max, entities_file_name, 7, node_num_max)
print("Load forest and nlp finished")

entities_list = set()
with open(entities_file_name+".csv", "r", encoding='utf-8') as csvfile:
    csvreader = csv.reader(csvfile, delimiter=',')
    for row in csvreader:
        if len(row) >= 2:
            entities_list.add(row[0].strip())
            entities_list.add(row[1].strip())

hash.cuckoo_build(tree_num_max, node_num_max)
print("Build Cuckoofilter finished")

print("Test Retrieval: ")
query = 'please introduce: '+ ' '.join(list(entities_list)[:50])
result = []

for num in range(10):
    start_time = time.time()
    for q in range(100):
        node_list = ruler.search_entity_info_cuckoofilter(nlp, query)
    end_time = time.time()
    execution_time = end_time - start_time
    print(f"\n\033[1;31m round={num+1} EntityTree search time: {execution_time:.6f} seconds\033[0m\n")
    result.append(execution_time)
    hash.cuckoo_sort()
