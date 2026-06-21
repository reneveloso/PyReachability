#pragma once
#include "reachability/csr_graph.hpp"
#include <vector>

namespace reachability {

// PReaCH — Pruned Reachability Contraction Hierarchies (Merz & Sanders, ESA 2014), on a DAG.
//
// An RCH ordering is built by repeatedly contracting source/sink vertices (smallest input
// degree first). Edges split into forward (order(u)<order(v)) and backward sets; by Theorem 1,
// s reaches t iff there is an "up-down" path, found by a bidirectional search that only walks
// to higher-order vertices and must meet. The search is pruned by forward/backward topological
// levels (Lemma 2) and a single-DFS interval range [phi, phi_hat] (Lemmas 3-4): the interval
// gives an exact positive/negative cut, levels an exact negative cut. (The extra empty/full
// ranges of Lemmas 5-7 are omitted — they only sharpen pruning, not correctness.)
//
// No public reference implementation was available; ported from the paper, verified against
// the BFS oracle.
class PReaCH {
public:
    PReaCH() = default;

    void build(const CSRGraph& dag);
    bool reaches(vid_t u, vid_t v);
    std::size_t index_size_bytes() const;

private:
    vid_t n_ = 0;
    CSRGraph fwd_, bwd_;            // forward up-edges; backward up-edges (v -> higher-order preds)
    std::vector<vid_t> lf_, lb_;    // forward / backward topological levels
    std::vector<vid_t> pf_, pf_hat_;  // forward DFS preorder and subtree max
    std::vector<vid_t> pb_, pb_hat_;  // backward DFS preorder and subtree max
    std::vector<int> vf_, vb_;      // per-query forward/backward visit stamps
    int query_cnt_ = 0;
};

}  // namespace reachability
