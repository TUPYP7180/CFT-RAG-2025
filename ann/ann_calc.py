import jieba
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import NearestNeighbors
from trag_tree import hash

class ANNMapping:
    def __init__(self):
        self.data = []  # 存储 (字符串, 实例)
        self.vectorizer = TfidfVectorizer(tokenizer=self.tokenize)
        self.nn_model = None

    def tokenize(self, text):
        return " ".join(jieba.cut(text))

    def add_instance(self, text, instance):
        self.data.append((text, instance))

    def build_index(self):
        """构建最近邻索引"""
        texts = [self.tokenize(text) for text, _ in self.data]
        self.vectorizer.fit(texts)
        vectors = self.vectorizer.transform(texts)

        self.nn_model = NearestNeighbors(n_neighbors=1, metric='cosine')
        self.nn_model.fit(vectors)

    def find_nearest(self, query_text):
        if self.nn_model is None:
            raise ValueError("Index not built. Call build_index() first.")
        
        query_vector = self.vectorizer.transform([self.tokenize(query_text)])
        distances, indices = self.nn_model.kneighbors(query_vector)

        return self.data[indices[0][0]][1]  # 返回最相近的类实例

mapper = ANNMapping()

def build_ann():
    for k, v in hash.node_hash.items():
        mapper.add_instance(k, v)
    mapper.build_index()

def find_ann(entity):
    return mapper.find_nearest(entity)
