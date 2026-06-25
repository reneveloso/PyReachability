#pragma once
#include "reachability/csr_graph.hpp"
#include "reachability/two_hop.hpp"
#include <vector>
#include <cstddef>

namespace reachability {

// HL — Hierarchical Labeling (Jin & Wang, "Simple, Fast, and Scalable Reachability Oracle",
// PVLDB 2013) on a DAG.
//
// HL builds a 2-hop oracle through a *recursive reachability backbone*, not a flat vertex order.
// A vertex hierarchy V0 = V ⊃ V1 ⊃ ... ⊃ Vh is formed where each Gi is the one-side reachability
// backbone of Gi-1; level(v) = i iff v in Vi\Vi+1. The core (top) is labeled first, then labels
// propagate down level by level (Algorithm 1): for v at level i,
//   Lout(v) = {v} U  union of Lout(w) over v's out-neighbours w in Gi
//   Lin(v)  = {v} U  union of Lin(w)  over v's in-neighbours  w in Gi
// and u reaches v iff Lout(u) and Lin(v) intersect. A *complete* index over the shared
// TwoHopLabels store (entries are vertex ids).
//
// The locality threshold is a parameter in the paper; here we use eps=1, for which the backbone
// is exactly a vertex cover (paper Example 4.1) — computed greedily by max degree, recursing
// until the core is edgeless. Then every neighbour of a level-i vertex lies in the backbone
// Vi+1, so the per-level rule above is Algorithm 1 with eps=1 (the paper focuses on eps=2 with
// its FastCover backbone — a documented simplification, not a change of semantics). No public
// reference implementation was available; ported from the paper, verified vs the BFS oracle.
class HL {
public:
    HL() = default;

    void build(const CSRGraph& dag);
    bool query(vid_t u, vid_t v) const;
    std::size_t index_size_bytes() const;

private:
    vid_t n_ = 0;
    TwoHopLabels L_;
    std::vector<vid_t> level_;   // topological level (quick negative cut)
};

}  // namespace reachability
