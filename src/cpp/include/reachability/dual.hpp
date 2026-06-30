#pragma once
#include "reachability/csr_graph.hpp"
#include <vector>
#include <cstddef>

namespace reachability {

// Dual Labeling — Wang, He, Yang, Yu & Yu, "Dual Labeling: Answering Graph Reachability Queries
// in Constant Time", ICDE 2006, on a DAG. Aimed at sparse graphs (few non-tree edges t).
//
// A spanning tree is preorder interval-labelled: vertex v gets [a, b) = [pre(v), pre(v)+size(v)),
// and w is a tree-descendant of v iff pre(w) in [a, b). The remaining reachability is carried by
// the *transitive link table* T: each non-tree edge (tail, head) becomes a link i -> [j, k) with
// i = pre(tail) and [j, k) = head's interval (superfluous links, where the head is already a
// tree-descendant of the tail, are dropped). T is closed under composition: links i1 -> [j1, k1)
// and i2 -> [j2, k2) with i2 in [j1, k1) yield i1 -> [j2, k2). By Theorem 1, u reaches v iff
// pre(v) in [a_u, b_u) (tree) or some link i -> [j, k) in T has i in [a_u, b_u) and pre(v) in
// [j, k). A *complete* index of size O(n + t^2). General graphs are reduced via SCC condensation.
//
// Faithful to the dual-label scheme and Theorem 1. The O(1) TLC counting function N(x, y) with
// gridding/snapping (paper Sec. 3.2-3.3) is a query-time accelerator and is represented here by a
// direct scan of the (small, for sparse graphs) link table; a plain DFS spanning tree is used
// instead of the optimum spanning tree of Sec. 5. Verified vs the BFS oracle.
class DualLabeling {
public:
    DualLabeling() = default;

    void build(const CSRGraph& dag);
    bool query(vid_t u, vid_t v) const;
    std::size_t index_size_bytes() const;

private:
    struct Link { vid_t i, j, k; };        // i -> [j, k)

    vid_t n_ = 0;
    std::vector<vid_t> pre_, a_, b_;        // preorder number; interval [a, b)
    std::vector<Link> tlc_;                 // transitive link table
};

}  // namespace reachability
