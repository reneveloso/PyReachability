#pragma once
#include "reachability/csr_graph.hpp"
#include <vector>
#include <cstddef>

namespace reachability {

// FERRARI — Seufert, Anand, Bedathur & Weikum, "FERRARI: Flexible and Efficient Reachability
// Range Assignment for Graph Indexing", ICDE 2013, on a DAG. A *partial* index (no false
// answers) generalising the interval labeling of Agrawal et al. and GRAIL.
//
// A spanning tree is post-order numbered; each vertex's reachable set is encoded as a set of
// post-order id intervals, computed by merging children's interval sets in reverse topological
// order. To respect a per-vertex budget of k intervals, adjacent intervals are merged across
// the smallest gaps (the FERRARI k-interval cover), minimising false positives. An interval is
// *exact* if it contains no unreachable id, else *approximate*. A query checks the target's id
// against the source's intervals: outside all -> not reachable; inside an exact one -> reachable;
// inside only approximate ones -> a guided DFS settles it (so the answer is always exact). A
// topological level filter gives an extra constant-time negative cut.
//
// Faithful to the core scheme (Ferrari-L, per-node budget). The paper's optional speed heuristics
// — seed-vertex pruning (S+/S-, see O'Reach for that flavour) and the global budget variant
// (Ferrari-G) — are omitted (documented simplification; same answers). Reference code exists
// (github.com/steps/Ferrari, CC BY-NC-SA) but this is an independent implementation from the
// paper. Verified vs the BFS oracle.
class Ferrari {
public:
    Ferrari() = default;

    void build(const CSRGraph& dag, int k);
    bool reaches(vid_t s, vid_t t);
    std::size_t index_size_bytes() const;

private:
    int check(vid_t v, vid_t pid) const;   // 0 none, 1 approximate, 2 exact

    vid_t n_ = 0;
    CSRGraph fwd_;
    std::vector<vid_t> pi_;                 // post-order number
    std::vector<vid_t> level_;              // topological level (quick negative cut)
    std::vector<std::vector<vid_t>> is_, ie_;  // per vertex: sorted interval starts / ends
    std::vector<std::vector<char>> iex_;       // per vertex: exact flag per interval
    std::vector<int> stamp_;                // guided-DFS per-query stamp
    int query_cnt_ = 0;
};

}  // namespace reachability
