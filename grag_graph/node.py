class EntityNode:

    def __init__(self, entity):
        self.entity = entity  # 实体名称
        self.neighbor = []  # 邻居节点

    def add_neighbor(self, node):
        self.neighbor.append(node)

    def get_neighbor(self):
        return self.neighbor

    def get_context(self):

        ancestors = self.get_neighbor()
        ancestor_length = len(ancestors)
        context = ""
        if ancestor_length > 0:
            context += f"在某个图型关系中，{self.entity}的邻居有："
            temp = []
            for level in range(ancestor_length-1, -1, -1):
                temp.append(ancestors[level].entity)
            context += "、".join(temp)

        context += "。"

        return context

    def get_entity(self):
        return self.entity
