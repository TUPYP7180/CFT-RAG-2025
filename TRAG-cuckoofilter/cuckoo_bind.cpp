#include <pybind11/pybind11.h>
#include <pybind11/stl.h>  
#include "cuckoofilter.h"  
#include "node.h"

namespace cuckoofilter {
    std::unordered_map<std::string, EntityInfo*> addr_map;
    EntityInfo * temp_info;
    EntityInfo * result_info;
    std::set<uint64_t> first_hash;
}

namespace py = pybind11;

PYBIND11_MODULE(cuckoo_filter_module, m) {

    py::enum_<cuckoofilter::Status>(m, "Status")
        .value("Ok", cuckoofilter::Status::Ok)
        .value("NotFound", cuckoofilter::Status::NotFound)
        .value("NotEnoughSpace", cuckoofilter::Status::NotEnoughSpace)
        .value("NotSupported", cuckoofilter::Status::NotSupported)
        .export_values();

    py::class_<cuckoofilter::EntityInfo>(m, "EntityInfo")
        .def(py::init<>())
        .def_readwrite("temperature", &cuckoofilter::EntityInfo::temperature)
        .def_readwrite("head", &cuckoofilter::EntityInfo::head); 

    py::class_<cuckoofilter::EntityStruct>(m, "EntityStruct")
        .def(py::init<>())
        .def_readwrite("content", &cuckoofilter::EntityStruct::content)
        .def("__index__", [](const cuckoofilter::EntityStruct &es) {
            return static_cast<uint64_t>(es);  
        });


    py::class_<cuckoofilter::CuckooFilter<cuckoofilter::EntityStruct, 12, cuckoofilter::SingleTable>>(m, "CuckooFilter")
        .def(py::init<size_t>(), py::arg("max_num_keys"))
        .def("add", &cuckoofilter::CuckooFilter<cuckoofilter::EntityStruct, 12, cuckoofilter::SingleTable>::Add, py::arg("item"), py::arg("info"))
        .def("extract", &cuckoofilter::CuckooFilter<cuckoofilter::EntityStruct, 12, cuckoofilter::SingleTable>::Extract, py::arg("item"))
        .def("sort", &cuckoofilter::CuckooFilter<cuckoofilter::EntityStruct, 12, cuckoofilter::SingleTable>::Sort)
        .def("build", &cuckoofilter::CuckooFilter<cuckoofilter::EntityStruct, 12, cuckoofilter::SingleTable>::BuildTree, py::arg("max_tree_num"), py::arg("max_node_num"));
}
