#include <iostream>
#include "Bloomfilter.h"

// g++ -std=c++17 -I./bloom_filter_cpp ./bloom_filter_cpp/main.cpp -o bloomfilter_program -lssl -lcrypto && ./bloomfilter_program
int main() {
    // 初始化布隆过滤器，使用 4 个哈希函数
    Bloomfilter bf(4);

    // 插入元素 "apple"
    bf.insert("apple");

    // 检查元素是否存在
    if (bf.contains("apple")) {
        std::cout << "apple 可能存在" << std::endl;
    } else {
        std::cout << "apple 不存在" << std::endl;
    }

    // 检查不存在的元素
    if (bf.contains("banana")) {
        std::cout << "banana 可能存在" << std::endl;
    } else {
        std::cout << "banana 不存在" << std::endl;
    }

    return 0;
}
