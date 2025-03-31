#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include "Bloomfilter.h"

namespace py = pybind11;

PYBIND11_MODULE(bloomfilter, m) {
    py::class_<Bloomfilter>(m, "Bloomfilter")
        .def(py::init<size_t>(), py::arg("hash_func_count") = 4)
        .def("insert", &Bloomfilter::insert)
        .def("contains", &Bloomfilter::contains)
        .def("clear", &Bloomfilter::clear)
        .def("object_count", &Bloomfilter::object_count)
        .def("empty", &Bloomfilter::empty);
}
