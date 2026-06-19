#include "reachability/csr_graph.hpp"
#include <algorithm>

namespace reachability {

CSRGraph::CSRGraph(vid_t n, const std::vector<vid_t>& src,
                   const std::vector<vid_t>& dst)
    : n_(n) {
    // Build adjacency, dropping self-loops.
    std::vector<std::vector<vid_t>> adj(static_cast<std::size_t>(n_));
    const std::size_t m = src.size();
    for (std::size_t i = 0; i < m; ++i) {
        vid_t u = src[i], v = dst[i];
        if (u == v) continue;                // drop self-loops
        adj[static_cast<std::size_t>(u)].push_back(v);
    }
    // Sort + unique each row (dedup multi-edges), then flatten to CSR.
    offsets_.assign(static_cast<std::size_t>(n_) + 1, 0);
    for (vid_t u = 0; u < n_; ++u) {
        auto& row = adj[static_cast<std::size_t>(u)];
        std::sort(row.begin(), row.end());
        row.erase(std::unique(row.begin(), row.end()), row.end());
        offsets_[static_cast<std::size_t>(u) + 1] =
            offsets_[static_cast<std::size_t>(u)] + row.size();
    }
    targets_.reserve(offsets_.back());
    for (vid_t u = 0; u < n_; ++u) {
        const auto& row = adj[static_cast<std::size_t>(u)];
        targets_.insert(targets_.end(), row.begin(), row.end());
    }
}

}  // namespace reachability
