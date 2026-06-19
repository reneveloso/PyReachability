#pragma once
#include "reachability/csr_graph.hpp"
#include <vector>

namespace reachability {

// FELINE reachability index (Veloso, Cerf, Meira Jr., Zaki, EDBT 2014), on a DAG.
//
// Each vertex gets a 2D coordinate (X, Y) from two topological orderings, forming a
// weak dominance drawing: r(u, v) => X[u] <= X[v] AND Y[u] <= Y[v]. The componentwise
// test is an exact negative cut; inconclusive pairs fall back to a dominance-pruned DFS.
class Feline {
public:
    Feline() = default;

    void build(const CSRGraph& dag);

    // Weak dominance: i(u) <= i(v). Necessary condition for r(u, v) (Theorem 1).
    bool dominates(vid_t u, vid_t v) const {
        return X_[u] <= X_[v] && Y_[u] <= Y_[v];
    }

    // Topological level (longest path from a root). u reaches v (u!=v) => level(u) < level(v).
    vid_t top_level(vid_t v) const { return level_[v]; }

    // Exact reachability: dominance negative cut, then dominance-pruned guided DFS.
    bool reaches(vid_t u, vid_t v);

    std::size_t index_size_bytes() const;

private:
    CSRGraph dag_;
    vid_t n_ = 0;
    std::vector<vid_t> X_, Y_;        // two topological-order ranks per vertex
    std::vector<vid_t> level_;        // topological level (longest path from a root)
    std::vector<int> visited_;        // per-query stamps for the guided DFS
    int query_cnt_ = 0;
};

}  // namespace reachability
