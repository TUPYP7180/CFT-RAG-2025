import ctypes
import os

# cd bloom_filter_cpp && rm libbloomfilter.so && g++ -std=c++17 -shared -fPIC -o libbloomfilter.so Bloomfilter.cpp -lssl -lcrypto && cd ..

# 加载 C++ 共享库，只需加载一次
current_dir = os.path.dirname(os.path.abspath(__file__))
so_path = os.path.join(current_dir, "..", "bloom_filter_cpp", "libbloomfilter.so")
print(so_path)
bloomfilter_lib = ctypes.CDLL(so_path)
# bloomfilter_lib = ctypes.CDLL("/volume/demo/wjliu/kq-rag-TRAG/bloom_filter_cpp/libbloomfilter.so")

# 定义 C++ BloomFilter 类的 Python 封装
class BloomFilterCPP:
    def __init__(self, hash_func_count=4):
        """初始化 C++ BloomFilter 实例"""
        self.obj = bloomfilter_lib.Bloomfilter_new(hash_func_count)

    def insert(self, item):
        """插入元素到 BloomFilter"""
        bloomfilter_lib.Bloomfilter_insert(self.obj, ctypes.c_char_p(item.encode()))

    def contains(self, item) -> bool:
        """检查元素是否存在于 BloomFilter 中"""
        result = bloomfilter_lib.Bloomfilter_contains(self.obj, ctypes.c_char_p(item.encode()))
        return bool(result)

    def clear(self):
        """清空 BloomFilter"""
        bloomfilter_lib.Bloomfilter_clear(self.obj)

    def object_count(self) -> int:
        """返回 BloomFilter 中对象的数量"""
        return bloomfilter_lib.Bloomfilter_object_count(self.obj)
    
    def empty(self) -> bool:
        """检查 BloomFilter 是否为空"""
        return bool(bloomfilter_lib.Bloomfilter_empty(self.obj))

