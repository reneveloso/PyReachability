#pragma once
#include "reachability/csr_graph.hpp"
#include <vector>
#include <utility>
#include <cstddef>

namespace reachability {

// Optimal Chain Cover — Chen & Chen, "An Efficient Algorithm for Answering Graph Reachability
// Queries", ICDE 2008, on a DAG. Like Chain Cover (Jagadish) but the DAG is decomposed into the
// *minimum* number of chains (the DAG width, by Dilworth's theorem), which yields smaller labels
// and faster queries than Jagadish's greedy decomposition.
//
// The minimum chain decomposition is the minimum chain partition of the reachability poset:
// |chains| = n - (maximum matching) in the bipartite graph with an edge u->v whenever u can reach
// v (Dilworth / Fulkerson). Each vertex then gets a (chain, position); since consecutive chain
// vertices are reachable, reaching a position implies reaching every later position on that chain,
// so each vertex records only the smallest reachable position per chain. u reaches v iff u's
// recorded min position on v's chain is <= pos(v). A *complete* index. General graphs are reduced
// via SCC condensation.
//
// Faithful to the scheme (minimum chains + the paper's index/index-sequence labeling). The minimum
// decomposition is computed by textbook maximum bipartite matching (Kuhn) over the reachability
// relation rather than Chen & Chen's stratification + virtual-node O(n^2 + bn*sqrt(b)) procedure —
// the same minimum number of chains. Construction uses reachability bitsets, so this targets
// small/medium graphs. Verified vs the BFS oracle.
class OptimalChainCover {
public:
    OptimalChainCover() = default;

    void build(const CSRGraph& dag);
    bool query(vid_t u, vid_t v) const;
    std::size_t index_size_bytes() const;

private:
    vid_t n_ = 0;
    std::vector<vid_t> chain_of_, pos_;
    std::vector<std::vector<std::pair<vid_t, vid_t>>> reach_;   // per vertex: sorted (chain, min pos)
};

}  // namespace reachability
