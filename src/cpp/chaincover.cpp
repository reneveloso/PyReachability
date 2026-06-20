#include "reachability/chaincover.hpp"
#include <algorithm>

namespace reachability {

void ChainCover::build(const CSRGraph& dag) {
    n_ = dag.num_nodes();
    chain_of_.assign(n_, -1);
    pos_.assign(n_, 0);
    reach_.assign(n_, {});

    // Topological order (Kahn).
    std::vector<vid_t> indeg(n_, 0);
    for (vid_t u = 0; u < n_; ++u)
        for (const vid_t* it = dag.out_begin(u); it != dag.out_end(u); ++it)
            ++indeg[*it];
    std::vector<vid_t> order;
    order.reserve(n_);
    {
        std::vector<vid_t> ind = indeg, q;
        for (vid_t u = 0; u < n_; ++u) if (ind[u] == 0) q.push_back(u);
        std::size_t head = 0;
        while (head < q.size()) {
            vid_t u = q[head++];
            order.push_back(u);
            for (const vid_t* it = dag.out_begin(u); it != dag.out_end(u); ++it)
                if (--ind[*it] == 0) q.push_back(*it);
        }
    }

    // Greedy edge-path cover: walk uncovered vertices into chains along out-edges.
    std::vector<char> covered(n_, 0);
    vid_t nchains = 0;
    for (vid_t s : order) {
        if (covered[s]) continue;
        vid_t cur = s, p = 0;
        const vid_t cid = nchains++;
        for (;;) {
            covered[cur] = 1;
            chain_of_[cur] = cid;
            pos_[cur] = p++;
            vid_t next = -1;
            for (const vid_t* it = dag.out_begin(cur); it != dag.out_end(cur); ++it)
                if (!covered[*it]) { next = *it; break; }
            if (next < 0) break;
            cur = next;
        }
    }

    // Reachable min-position per chain, in reverse topological order.
    std::vector<std::pair<vid_t, vid_t>> buf;
    for (std::size_t i = order.size(); i-- > 0;) {
        vid_t v = order[i];
        buf.clear();
        buf.emplace_back(chain_of_[v], pos_[v]);
        for (const vid_t* it = dag.out_begin(v); it != dag.out_end(v); ++it)
            for (const auto& e : reach_[*it]) buf.push_back(e);
        std::sort(buf.begin(), buf.end());            // by chain, then position
        auto& out = reach_[v];
        for (const auto& e : buf) {
            if (!out.empty() && out.back().first == e.first) {
                if (e.second < out.back().second) out.back().second = e.second;
            } else {
                out.push_back(e);                      // first (= smallest pos) for this chain
            }
        }
    }
}

bool ChainCover::query(vid_t u, vid_t v) const {
    if (u == v) return true;
    const vid_t c = chain_of_[v], p = pos_[v];
    const auto& r = reach_[u];
    // binary search the entry for chain c
    std::size_t lo = 0, hi = r.size();
    while (lo < hi) {
        std::size_t mid = (lo + hi) / 2;
        if (r[mid].first < c) lo = mid + 1; else hi = mid;
    }
    if (lo < r.size() && r[lo].first == c) return r[lo].second <= p;
    return false;
}

std::size_t ChainCover::index_size_bytes() const {
    std::size_t bytes = (chain_of_.size() + pos_.size()) * sizeof(vid_t);
    for (const auto& r : reach_) bytes += r.size() * 2 * sizeof(vid_t);
    return bytes;
}

}  // namespace reachability
