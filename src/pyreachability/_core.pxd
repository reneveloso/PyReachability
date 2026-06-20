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
        const vid_t* out_begin(vid_t) const
        const vid_t* out_end(vid_t) const

cdef extern from "reachability/bfsdfs.hpp" namespace "reachability":
    cbool bfs_reaches(const CSRGraph&, vid_t, vid_t) nogil

cdef extern from "reachability/scc.hpp" namespace "reachability":
    cdef cppclass Condensation:
        vector[vid_t] comp
        vid_t num_comp
        CSRGraph dag
        vector[vid_t] topo_order
    Condensation scc_condense(const CSRGraph&) except +

cdef extern from "reachability/grail.hpp" namespace "reachability":
    cdef cppclass Grail:
        Grail() except +
        void build(const CSRGraph&, int, unsigned int, cbool) except +
        cbool reaches(vid_t, vid_t) nogil
        size_t index_size_bytes()
        int dim()

cdef extern from "reachability/feline.hpp" namespace "reachability":
    cdef cppclass Feline:
        Feline() except +
        void build(const CSRGraph&, cbool) except +
        cbool reaches(vid_t, vid_t) nogil
        size_t index_size_bytes()
