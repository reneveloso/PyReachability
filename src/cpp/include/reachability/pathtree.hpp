#pragma once
#include "reachability/csr_graph.hpp"
#include <vector>
#include <cstddef>

namespace reachability {

// Path-Tree — Jin, Ruan, Xiang & Wang, "Path-Tree: An Efficient Reachability Indexing Scheme for
// Large Directed Graphs", ACM TODS 2011, on a DAG. A generalisation of the tree cover where the
// covering structure is a tree of *paths* (a path-tree cover).
//
// Construction: (1) decompose the DAG into paths (Simon's algorithm), giving each vertex (pid,
// sid); (2) form the path-graph (a node per path, an edge per connected path-pair); (3) take a
// spanning arborescence (SP-tree) of it; (4) label the path-tree cover with a 3-tuple
// (X, I.begin, I.end): X by a post-order DFS over the cover (Algorithm 2), I the SP-tree interval
// of a vertex's path. By Lemma 4, u reaches v *within the cover* iff X(u) <= X(v) and v's path
// interval is contained in u's. (5) The reachability not captured by the cover is compressed into
// a per-vertex residual set Rc(u) (Algorithm 3). A query is then: u reaches v iff coverReach(u, v),
// or coverReach(x, v) for some x in Rc(u). A *complete* index. General graphs are reduced via SCC
// condensation.
//
// Independent implementation from the paper (no public reference code). Documented simplifications
// (affecting index size, not correctness): the minimal-equivalent-edge-set step is skipped (all
// edges of an SP-tree path-pair are used — reachability-equivalent); the SP-tree is a greedy
// spanning arborescence rather than Edmonds' maximum-weight one; the residual is scanned linearly
// (vs the paper's O(log^2 k)). Verified vs the BFS oracle.
class PathTree {
public:
    PathTree() = default;

    void build(const CSRGraph& dag);
    bool query(vid_t u, vid_t v) const;
    std::size_t index_size_bytes() const;

private:
    // u reaches v using only the path-tree cover (Lemma 4)
    bool cover_reach(vid_t u, vid_t v) const {
        return x_[u] <= x_[v] &&
               ib_[pid_[u]] <= ib_[pid_[v]] && ie_[pid_[v]] <= ie_[pid_[u]];
    }

    vid_t n_ = 0;
    std::vector<vid_t> pid_, x_;            // path id; DFS X label
    std::vector<vid_t> ib_, ie_;            // per-path SP-tree interval [begin, end]
    std::vector<std::vector<vid_t>> rc_;    // residual transitive-closure representatives per vertex
};

}  // namespace reachability
