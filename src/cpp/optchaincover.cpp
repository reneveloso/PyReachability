#include "reachability/optchaincover.hpp"
#include <algorithm>
#include <cstdint>
#include <vector>

namespace reachability {

void OptimalChainCover::build(const CSRGraph& dag) {
    n_ = dag.num_nodes();
    chain_of_.assign(n_, -1); pos_.assign(n_, 0);
    reach_.assign(n_, {});
    if (n_ == 0) return;

    // topological order (Kahn)
    std::vector<vid_t> indeg(n_, 0);
    for (vid_t u = 0; u < n_; ++u)
        for (const vid_t* it = dag.out_begin(u); it != dag.out_end(u); ++it) ++indeg[*it];
    std::vector<vid_t> topo; topo.reserve(n_);
    {
        std::vector<vid_t> ind = indeg, q;
        for (vid_t u = 0; u < n_; ++u) if (ind[u] == 0) q.push_back(u);
        std::size_t h = 0;
        while (h < q.size()) { vid_t u = q[h++]; topo.push_back(u);
            for (const vid_t* it = dag.out_begin(u); it != dag.out_end(u); ++it)
                if (--ind[*it] == 0) q.push_back(*it); }
    }

    // reachability bitsets: desc[v] = vertices reachable from v (incl. v), reverse topo closure
    const vid_t W = (n_ + 63) / 64;
    std::vector<std::uint64_t> desc((std::size_t)n_ * W, 0);
    auto dset = [&](vid_t r, vid_t b){ desc[(std::size_t)r * W + (b >> 6)] |= (std::uint64_t)1 << (b & 63); };
    for (std::size_t i = topo.size(); i-- > 0;) {
        vid_t v = topo[i]; dset(v, v);
        for (const vid_t* it = dag.out_begin(v); it != dag.out_end(v); ++it) {
            std::uint64_t* dv = &desc[(std::size_t)v * W];
            const std::uint64_t* dw = &desc[(std::size_t)(*it) * W];
            for (vid_t k = 0; k < W; ++k) dv[k] |= dw[k];
        }
    }

    // minimum chain partition = n - maximum bipartite matching, edge u->v iff u reaches v (u!=v)
    // (Dilworth). Kuhn's augmenting-path matching; matchR[v] = left vertex matched to right v.
    std::vector<vid_t> matchR(n_, -1), matchL(n_, -1);
    std::vector<char> seen(n_);
    for (vid_t s : topo) {
        std::fill(seen.begin(), seen.end(), 0);
        // recursive Kuhn augmenting search (graphs here are small/medium)
        struct Aug {
            const std::vector<std::uint64_t>& desc; vid_t W, n;
            std::vector<vid_t>& matchR; std::vector<char>& seen;
            bool run(vid_t u) {
                for (vid_t v = 0; v < n; ++v) {
                    if (v == u || seen[v]) continue;
                    if (!((desc[(std::size_t)u * W + (v >> 6)] >> (v & 63)) & 1ULL)) continue;  // u !-> v
                    seen[v] = 1;
                    if (matchR[v] == -1 || run(matchR[v])) { matchR[v] = u; return true; }
                }
                return false;
            }
        } aug{desc, W, n_, matchR, seen};
        aug.run(s);
    }
    for (vid_t v = 0; v < n_; ++v) if (matchR[v] != -1) matchL[matchR[v]] = v;

    // build chains: heads are vertices with no chain predecessor (matchR == -1), follow matchL
    vid_t nchains = 0;
    for (vid_t h = 0; h < n_; ++h) {
        if (matchR[h] != -1) continue;            // not a chain head
        vid_t cur = h, p = 0; const vid_t cid = nchains++;
        while (cur != -1) {
            chain_of_[cur] = cid; pos_[cur] = p++;
            cur = matchL[cur];
        }
    }

    // per-vertex reachable min position per chain, in reverse topological order (as in Chain Cover)
    std::vector<std::pair<vid_t, vid_t>> buf;
    for (std::size_t i = topo.size(); i-- > 0;) {
        vid_t v = topo[i];
        buf.clear();
        buf.emplace_back(chain_of_[v], pos_[v]);
        for (const vid_t* it = dag.out_begin(v); it != dag.out_end(v); ++it)
            for (const auto& e : reach_[*it]) buf.push_back(e);
        std::sort(buf.begin(), buf.end());
        auto& out = reach_[v];
        for (const auto& e : buf) {
            if (!out.empty() && out.back().first == e.first) {
                if (e.second < out.back().second) out.back().second = e.second;
            } else out.push_back(e);
        }
    }
}

bool OptimalChainCover::query(vid_t u, vid_t v) const {
    if (u == v) return true;
    const vid_t c = chain_of_[v], p = pos_[v];
    const auto& r = reach_[u];
    std::size_t lo = 0, hi = r.size();
    while (lo < hi) { std::size_t mid = (lo + hi) / 2; if (r[mid].first < c) lo = mid + 1; else hi = mid; }
    if (lo < r.size() && r[lo].first == c) return r[lo].second <= p;
    return false;
}

std::size_t OptimalChainCover::index_size_bytes() const {
    std::size_t bytes = (chain_of_.size() + pos_.size()) * sizeof(vid_t);
    for (const auto& r : reach_) bytes += r.size() * 2 * sizeof(vid_t);
    return bytes;
}

}  // namespace reachability
