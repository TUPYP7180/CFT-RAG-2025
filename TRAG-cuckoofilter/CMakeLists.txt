cmake_minimum_required(VERSION 3.4)
project(cuckoo_filter)

set(CMAKE_CXX_STANDARD 11)

find_package(pybind11 REQUIRED)

include_directories(${CMAKE_SOURCE_DIR}/src)

pybind11_add_module(cuckoo_filter_module
    cuckoo_bind.cpp
)
