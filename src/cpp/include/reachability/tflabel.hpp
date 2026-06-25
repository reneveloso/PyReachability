#pragma once
#include "reachability/csr_graph.hpp"
#include "reachability/two_hop.hpp"
#include <vector>
#include <cstddef>

namespace reachability {

// TF-Label — Topological-Folding Labeling (Cheng, Huang, Wu, Fu, SIGMOD 2013) on a DAG.
//
// A 2-hop labeling whose construction is a *topological folding*: vertices are placed on
// topological levels and the DAG is repeatedly folded in half — each fold removes the
// odd-level vertices and reconnects their in-neighbours straight to their out-neighbours —
// so a vertex is processed in O(lg L) folds instead of all L levels. The "TF number" tf(v) is
// the last fold that still contains v. Labels follow Definition 5: labelout(v) is the closure
// of v under "out-neighbours in the folding graph at tf(u)" (which, by Lemma 5, always have a
// strictly larger tf, so the closure is shallow); labelin(v) symmetrically. u reaches v iff
// labelout(u) and labelin(v) intersect (Equation 1) — a *complete* index over the shared
// TwoHopLabels store.
//
// Cross-level edges: the paper keeps the graph compact with lazily-created, shared dummy
// vertices (Procedure 1). Here they are made level-consecutive by *edge subdivision* (a dummy
// per intermediate level), which makes the graph L-partite so the basic folding is exact. This
// is faithful to the folding scheme and Definition 5 / Equation 1 but produces larger labels
// than the optimised version, so it targets small/medium graphs (like TC / TreeCover). No
// public reference implementation was available; ported from the paper, verified vs the BFS
// oracle.
class TFLabel {
public:
    TFLabel() = default;

    void build(const CSRGraph& dag);
    bool query(vid_t u, vid_t v) const;
    std::size_t index_size_bytes() const;

private:
    vid_t n_ = 0;
    TwoHopLabels L_;
    std::vector<vid_t> level_;   // 0-indexed topological level (quick negative cut)
};

}  // namespace reachability
