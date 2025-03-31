from trag_tree.node import EntityNode
from queue import Queue
from pybloom_live import BloomFilter


node_record = {}


class EntityTree:

    def __init__(self, root_entity, data):

        self.root = EntityNode(root_entity)

        edges = {}
        self.layer_filters = []
        for edge in data:
            if edge[0] not in edges:
                edges[edge[0]] = set()
            if edge[1] not in edges:
                edges[edge[1]] = set()
            edges[edge[0]].add(edge[1])
            edges[edge[1]].add(edge[0])

        temp_queue = Queue()
        temp_queue.put(self.root)
        vis = {}
        current_layer = []
        next_layer = []
        self.all_nodes = {}

        while not temp_queue.empty():
            front = temp_queue.get()
            vis[front.get_entity()] = 1
            current_layer.append(front)
            self.all_nodes[front.get_entity()] = front

            for sub_node in edges[front.get_entity()]:
                if sub_node is not None and sub_node != front.get_entity():
                    if front.get_parent() is None or ( front.get_parent() is not None \
                            and sub_node != front.get_parent().get_entity()):
                        if sub_node in vis:  # 无向有环图，不是树
                            # self.root = None
                            # print("检测到要出现环路，暂时移除此边")
                            pass
                        else:
                            new_node = EntityNode(sub_node)
                            front.add_children(new_node)
                            next_layer.append(new_node)
                            temp_queue.put(new_node)

            if temp_queue.empty() and next_layer:
                for node in current_layer:
                    if node.get_children():     # 每个节点，有该节点的所有子节点构成的BloomFilter
                        node.set_bloom_filter(node.get_all_descendants())
                current_layer = next_layer
                next_layer = []
        # self.build_layer_filters()

    def build_layer_filters(self):
        # 获取到每一层的节点
        node_layers = {}
        for node in self.all_nodes.values():
            level = self.get_node_level(node)
            if level not in node_layers:
                node_layers[level] = []
            node_layers[level].append(node)

        # 将每一层的节点以及子节点放入bloomfilter
        max_level = max(node_layers.keys())
        for level in range(max_level, -1, -1):  # 从下往上逆序遍历，这样可以复用下层的bloomfilter信息
            layer_bloom_filter = BloomFilter(capacity=4000)
            for node in node_layers[level]:
                for entity in node.get_all_descendants():
                    layer_bloom_filter.add(entity)
                layer_bloom_filter.add(node.get_entity())
            self.layer_filters.insert(0, layer_bloom_filter)

    def get_node_level(self, node):
        level = 0
        while node.get_parent() is not None:
            level += 1
            node = node.get_parent()
        return level

    def set_bitset(self, hash_func):
        temp_queue = Queue()
        temp_queue.put(self.root)
        while not temp_queue.empty():
            front = temp_queue.get()
            front.set_bitset(hash_func)
            for sub_node in front.get_children():
                if sub_node is not None:
                    temp_queue.put(sub_node)

    def get_root(self):
        return self.root

    def print_tree(self):
        temp_queue = Queue()
        temp_queue.put(self.root)
        hierarchy = 0
        while not temp_queue.empty():
            print("hierarchy: "+str(hierarchy), end=" ")
            temp_queue_peer = Queue()
            while not temp_queue.empty():
                front = temp_queue.get()
                print(front.get_entity()+" ", end=" ")
                for sub_node in front.get_children():
                    if sub_node is not None:
                        temp_queue_peer.put(sub_node)
            while not temp_queue_peer.empty():
                temp_queue.put(temp_queue_peer.get())
            print("")
            hierarchy += 1

    def bfs_search(self, entity):
        if self.root is None:
            return None
        temp_queue = Queue()
        temp_queue.put(self.root)
        while not temp_queue.empty():
            front = temp_queue.get()
            if front.get_entity() == entity:
                return front
            for sub_node in front.get_children():
                if sub_node is not None:
                    temp_queue.put(sub_node)
        return None

    def bfs_search2(self, entity):
        if self.root is None:
            return None
        temp_queue = Queue()
        temp_queue.put(self.root)
        while not temp_queue.empty():
            front = temp_queue.get()
            # print(f"front: {front.get_entity()}")
            if front.get_entity() == entity:
                return front
             # 如果该节点的子节点都不存在entity，则不入队，该节点下的分支都剪掉
            if front.get_children() and entity not in front.get_bloom_filter():
                continue  
            for sub_node in front.get_children():
                if sub_node is not None:
                    temp_queue.put(sub_node)
        return None
     
    def layer_search(self, entity):
        if self.root is None:
            return None
        layer_index = 0
        temp_queue = Queue()
        temp_queue.put(self.root)

        while not temp_queue.empty():
            current_layer_size = temp_queue.qsize()
            if entity not in self.layer_filters[layer_index]:  # 一定不存在
                return None

            for _ in range(current_layer_size):  # 可能存在
                front = temp_queue.get()
                if front.get_entity() == entity: 
                    return front 
                
                for sub_node in front.get_children(): 
                    if sub_node is not None:
                        temp_queue.put(sub_node)

            layer_index += 1
        return None