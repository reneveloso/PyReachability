#pragma once
#include "reachability/csr_graph.hpp"
#include <vector>

namespace reachability {

struct Condensation {
    std::vector<vid_t> comp;        // comp[v] = component id of vertex v
    vid_t num_comp = 0;
    CSRGraph dag;                   // condensed DAG over component ids
    std::vector<vid_t> topo_order;  // component ids in topological order
};

Condensation scc_condense(const CSRGraph& g);

}  // namespace reachability
