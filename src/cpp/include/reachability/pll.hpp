#pragma once
#include "reachability/csr_graph.hpp"
#include <vector>

namespace reachability {

// PLL — Pruned Landmark Labeling (Yano, Akiba, Iwata, Yoshida, CIKM 2013), on a DAG.
//
// A 2-hop labeling: each vertex v keeps L_out(v) = landmarks v reaches and L_in(v) =
// landmarks that reach v (stored as sorted landmark ranks). u reaches v iff the two sets
// share a landmark. It is a *complete* index — no fallback search.
class PLL {
public:
    PLL() = default;

    void build(const CSRGraph& dag);

    // Exact reachability on the DAG.
    bool query(vid_t u, vid_t v) const;

    std::size_t index_size_bytes() const;

private:
    vid_t n_ = 0;
    std::vector<std::vector<vid_t>> reach_to_;    // L_out: landmark ranks each vertex reaches
    std::vector<std::vector<vid_t>> reach_from_;  // L_in: landmark ranks that reach each vertex
    std::vector<vid_t> level_;                    // topological level (quick negative cut)

    // sorted-merge intersection of L_out(s) and L_in(t)
    bool intersects(vid_t s, vid_t t) const;
};

}  // namespace reachability
