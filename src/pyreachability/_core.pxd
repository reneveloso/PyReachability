# distutils: language = c++
# C++ declarations shared across the Cython module live here as the project grows.
from libcpp.vector cimport vector
from libcpp cimport bool as cbool

cdef extern from "reachability/csr_graph.hpp" namespace "reachability":
    ctypedef int vid_t
    cdef cppclass CSRGraph:
        CSRGraph() except +
        CSRGraph(vid_t, const vector[vid_t]&, const vector[vid_t]&) except +
        vid_t num_nodes() const
        size_t num_edges() const

cdef extern from "reachability/bfsdfs.hpp" namespace "reachability":
    cbool bfs_reaches(const CSRGraph&, vid_t, vid_t)
