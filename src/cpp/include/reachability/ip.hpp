#pragma once
#include "reachability/csr_graph.hpp"
#include <vector>
#include <cstddef>

namespace reachability {

// IP — Wei, Yu & Lu, "Reachability Querying: An Independent Permutation Labeling Approach",
// PVLDB 2014, on a DAG. A *partial* (Label+G) index: sound negative cuts from randomized
// permutation labels, with a guided DFS settling the rest.
//
// u reaches v requires Out(v) subset Out(u) and In(u) subset In(v) (Out/In are the reachable /
// reaching sets). For each of np independent permutations pi, every vertex stores mink — the k
// smallest pi-values of its Out set and of its In set (k-min-wise). By Theorem 4.1, if
// mink(pi(Out(u))) "succ" mink(pi(Out(v))) (some pi-value in v's k-min Out is provably absent
// from u's), then Out(v) is not a subset of Out(u), hence u cannot reach v; symmetrically for In.
// Any permutation firing this test answers the query negatively in constant time. A topological
// level filter adds another sound negative cut. Inconclusive queries fall back to a guided DFS
// that prunes with the same cuts, so the answer is always exact. General graphs are reduced via
// SCC condensation.
//
// Faithful to the k-min-wise scheme; of the paper's two additional DFS-reduction labels we keep
// the topological level and omit the interval label (a speed optimisation). Verified vs the BFS
// oracle.
class IP {
public:
    IP() = default;

    // k: top-k per permutation; np: number of permutations; seed: RNG seed.
    void build(const CSRGraph& dag, int k, int np, unsigned seed);
    bool reaches(vid_t u, vid_t v);
    std::size_t index_size_bytes() const;

private:
    int neg_cut(vid_t u, vid_t v) const;   // 1 if certainly u !-> v, else 0

    vid_t n_ = 0;
    int k_ = 2, np_ = 2;
    CSRGraph fwd_;
    std::vector<vid_t> level_;                  // forward topological level
    std::vector<std::vector<vid_t>> lout_, lin_;  // [p*n+v] -> sorted up-to-k smallest pi-values
    std::vector<int> stamp_;
    int query_cnt_ = 0;
};

}  // namespace reachability
