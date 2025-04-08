from pybloom_live import BloomFilter
import os
import sys
import ctypes

# from bloom_filter_py import BloomFilterCPP

# cd bloom_filter_cpp && rm -r build && mkdir build && cd build && cmake .. && make && cd ../..
current_dir = os.path.dirname(os.path.abspath(__file__))
so_path = os.path.join(current_dir, "..", "bloom_filter_cpp", "build")
# sys.path.append(current_dir)
sys.path.append(so_path)
import bloomfilter

class EntityNode:

    def __init__(self, entity, search_method=2):
        self.entity = entity  # 实体名称
        self.bitset = 0  # BF

        self.parent = None  # 父节点
        self.children = []  # 子节点

        self.bloom_filter = None
        
        self.is_last_but_one_layer = False
        self.search_method = search_method

    def set_bitset(self, hash_func):
        self.bitset = hash_func(self.entity)

    def add_children(self, node):
        node.parent = self
        self.children.append(node)

    def get_children(self):
        return self.children

    def get_parent(self):
        return self.parent

    def get_ancestors(self):
        ancestors = []
        ancestor = self.parent
        while ancestor != None:
            ancestors.append(ancestor)
            ancestor = ancestor.parent
        return ancestors

    def get_context(self):

        ancestors = self.get_ancestors()
        ancestor_length = len(ancestors)
        context = ""
        if ancestor_length > 0:
            ancestor_length = min(3, ancestor_length)
            context += f"在某个树型关系中，{self.entity}的向上的层级关系有："
            temp = []
            for level in range(ancestor_length-1, -1, -1):
                temp.append(ancestors[level].entity)
            context += "、".join(temp)

        children = self.get_children()
        children_length = len(children)
        if children_length > 0:
            if ancestor_length > 0:
                context += "；"
            context += f"{self.entity}的向下的子节点有："
            context += "、".join([e.get_entity() for e in children])

        context += "。"

        return context

    def get_bitset(self):
        return self.bitset

    def get_entity(self):
        return self.entity

    def get_bloom_filter(self):
        return self.bloom_filter

    def set_bloom_filter(self, entities):
        """为当前节点设置 Bloom Filter"""
        if self.search_method == 6:
            self.bloom_filter = bloomfilter.Bloomfilter()
            for entity in entities:
                self.bloom_filter.insert(entity)
        else:
            self.bloom_filter = BloomFilter(capacity=30000)
            for entity in entities:
                self.bloom_filter.add(entity)
        
    
    def set_is_last_but_one_layer(self):
        self.is_last_but_one_layer = True
        
    def get_is_last_but_one_layer(self):
        return self.is_last_but_one_layer

    def get_all_descendants(self):
        """递归获取当前节点的所有后代节点"""
        descendants = set()
        for child in self.children:
            descendants.add(child.get_entity())  # 添加直接子节点
            descendants.update(child.get_all_descendants())  # 添加子孙节点
        return descendants
