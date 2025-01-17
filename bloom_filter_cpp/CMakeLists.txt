cmake_minimum_required(VERSION 3.12)
project(bloomfilter_python)

set(CMAKE_CXX_STANDARD 17)

find_package(Python3 COMPONENTS Interpreter Development REQUIRED)
find_package(pybind11 REQUIRED)
find_package(OpenSSL REQUIRED)

add_library(bloomfilter SHARED bloomfilter_bind.cpp)

# 链接 pybind11 和 OpenSSL
target_link_libraries(bloomfilter PRIVATE pybind11::module OpenSSL::SSL OpenSSL::Crypto)

# 设置生成的共享库的前缀为空，生成 bloomfilter.so 而不是 libbloomfilter.so
set_target_properties(bloomfilter PROPERTIES PREFIX "")

# 包含头文件目录
target_include_directories(bloomfilter PRIVATE ${CMAKE_SOURCE_DIR})

