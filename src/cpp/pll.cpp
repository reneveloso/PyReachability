#include "reachability/pll.hpp"
#include "reachability/levels.hpp"
#include <algorithm>
#include <utility>

namespace reachability {

void PLL::build(const CSRGraph& dag) {
    n_ = dag.num_nodes();
    L_.resize(n_);
    level_ = topological_levels(dag);

    // reverse adjacency (in-edges) for the backward pruned BFS
    CSRGraph rdag;
    {
        std::vector<vid_t> rs, rd;
        rs.reserve(dag.num_edges());
        rd.reserve(dag.num_edges());
        for (vid_t u = 0; u < n_; ++u)
            for (const vid_t* it = dag.out_begin(u); it != dag.out_end(u); ++it) {
                rs.push_back(*it); rd.push_back(u);
            }
        rdag = CSRGraph(n_, rs, rd);
    }

    // landmark order: (indeg+1)*(outdeg+1) descending
    std::vector<std::pair<long long, vid_t>> ord(n_);
    for (vid_t v = 0; v < n_; ++v) {
        long long deg = (long long)(dag.out_degree(v) + 1) *
                        (long long)(rdag.out_degree(v) + 1);
        ord[v] = {deg, v};
    }
    std::sort(ord.begin(), ord.end(), std::greater<std::pair<long long, vid_t>>());

    std::vector<char> visited(n_, 0);
    std::vector<vid_t> q(n_);

    for (vid_t i = 0; i < n_; ++i) {
        const vid_t start = ord[i].second;

        // forward pruned BFS over out-edges -> fills L_in
        vid_t qs = 0, qt = 0;
        q[qt++] = start;
        while (qs != qt) {
            vid_t v = q[qs++];
            if (two_hop_intersects(L_, start, v)) continue;   // already decided -> prune
            L_.Lin[v].push_back(i);
            for (const vid_t* it = dag.out_begin(v); it != dag.out_end(v); ++it)
                if (!visited[*it]) { visited[*it] = 1; q[qt++] = *it; }
        }
        for (vid_t j = 0; j < qt; ++j) visited[q[j]] = 0;

        // reverse pruned BFS over in-edges -> fills L_out
        qs = qt = 0;
        q[qt++] = start;
        while (qs != qt) {
            vid_t v = q[qs++];
            if (two_hop_intersects(L_, v, start)) continue;   // already decided -> prune
            L_.Lout[v].push_back(i);
            for (const vid_t* it = rdag.out_begin(v); it != rdag.out_end(v); ++it)
                if (!visited[*it]) { visited[*it] = 1; q[qt++] = *it; }
        }
        for (vid_t j = 0; j < qt; ++j) visited[q[j]] = 0;

        visited[start] = 1;   // canonical ordering: remove processed landmark from later BFS
    }
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
