#include "reachability/pll.hpp"
#include "reachability/levels.hpp"
#include <algorithm>
#include <utility>

namespace reachability {

void PLL::build(const CSRGraph& dag) {
    n_ = dag.num_nodes();
    level_ = topological_levels(dag);

    // in-degrees for the degree-product landmark order
    std::vector<vid_t> indeg(n_, 0);
    for (vid_t u = 0; u < n_; ++u)
        for (const vid_t* it = dag.out_begin(u); it != dag.out_end(u); ++it)
            ++indeg[*it];

    // landmark order: (indeg+1)*(outdeg+1) descending (ties by larger vertex id)
    std::vector<std::pair<long long, vid_t>> ord(n_);
    for (vid_t v = 0; v < n_; ++v) {
        long long deg = (long long)(dag.out_degree(v) + 1) * (long long)(indeg[v] + 1);
        ord[v] = {deg, v};
    }
    std::sort(ord.begin(), ord.end(), std::greater<std::pair<long long, vid_t>>());

    std::vector<vid_t> order(n_);
    for (vid_t i = 0; i < n_; ++i) order[i] = ord[i].second;

    build_two_hop_labels(dag, order, L_);
}

bool PLL::query(vid_t u, vid_t v) const {
    if (u == v) return true;
    if (level_[u] >= level_[v]) return false;   // topological quick reject
    return two_hop_intersects(L_, u, v);
}

std::size_t PLL::index_size_bytes() const {
    return L_.size_bytes() + level_.size() * sizeof(vid_t);
}

}  // namespace reachability
