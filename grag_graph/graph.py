from grag_graph.node import EntityNode
from trag_tree import hash
import csv

def build_graph(entities_file_name):

    print('build graph...')

    rel = []
    entities_list = set()
    with open(entities_file_name+".csv", "r", encoding='utf-8') as csvfile:
        csvreader = csv.reader(csvfile, delimiter=',')
        for row in csvreader:
            if len(row) >= 2:
                rel.append({'subject': row[0].strip(), 'object': row[1].strip()})
                entities_list.add(row[0].strip())
                entities_list.add(row[1].strip())

    data = []
    cnt = 0

    for dependency in rel:
        data.append([dependency['subject'].lower().strip(), dependency['object'].lower().strip()])

    for edge in data:

        entity_1 = edge[0]
        entity_2 = edge[1]

        e1 = None
        e2 = None

        if entity_1 in hash.node_hash:
            e1 = hash.node_hash[entity_1][0]
        else:
            cnt += 1
            e1 = EntityNode(entity_1)
            hash.node_hash[entity_1] = []
            hash.node_hash[entity_1].append(e1)
        
        if entity_2 in hash.node_hash:
            e2 = hash.node_hash[entity_2][0]
        else:
            cnt += 1
            e2 = EntityNode(entity_2)
            hash.node_hash[entity_2] = []
            hash.node_hash[entity_2].append(e2)

        e1.add_neighbor(e2)
        e2.add_neighbor(e1)

    print(f'build graph complete, node number: {cnt}')
