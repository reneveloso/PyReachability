#include "reachability/treecover.hpp"
#include "reachability/optimal_tree.hpp"
#include <algorithm>

namespace reachability {

void TreeCover::build(const CSRGraph& dag) {
    n_ = dag.num_nodes();
    post_.assign(n_, 0);
    intervals_.assign(n_, {});
    if (n_ == 0) return;

    // Agrawal's optimum tree cover: pick each node's tree parent to minimise total intervals.
    std::vector<vid_t> parent = optimal_tree_parent(dag);
    std::vector<std::vector<vid_t>> children(n_);
    for (vid_t v = 0; v < n_; ++v) if (parent[v] != -1) children[parent[v]].push_back(v);

    // Post-order numbering over the optimum tree, so each subtree is a contiguous interval.
    {
        struct F { vid_t v; std::size_t ci; };
        std::vector<F> st;
        vid_t counter = 0;
        for (vid_t r = 0; r < n_; ++r) {
            if (parent[r] != -1) continue;
            st.push_back({r, 0});
            while (!st.empty()) {
                F& f = st.back();
                if (f.ci < children[f.v].size()) st.push_back({children[f.v][f.ci++], 0});
                else { post_[f.v] = counter++; st.pop_back(); }
            }
        }
    }

    // Reverse topological order (every successor before v) for merging interval sets.
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

    // I[v] = merge( {[post[v],post[v]]} U over successors w: I[w] ), in reverse topological order.
    std::vector<std::pair<vid_t, vid_t>> buf;
    for (std::size_t fi = topo.size(); fi-- > 0;) {
        vid_t v = topo[fi];
        buf.clear();
        buf.emplace_back(post_[v], post_[v]);
        for (const vid_t* it = dag.out_begin(v); it != dag.out_end(v); ++it)
            for (const auto& iv : intervals_[*it]) buf.push_back(iv);
        std::sort(buf.begin(), buf.end());
        auto& out = intervals_[v];
        for (const auto& iv : buf) {
            if (!out.empty() && iv.first <= out.back().second + 1) {
                if (iv.second > out.back().second) out.back().second = iv.second;
            } else {
                out.push_back(iv);
            }
        }
    }
}

bool TreeCover::query(vid_t u, vid_t v) const {
    if (u == v) return true;
    const vid_t p = post_[v];
    const auto& iv = intervals_[u];
    // binary search for the interval whose lo <= p
    std::size_t lo = 0, hi = iv.size();
    while (lo < hi) {
        std::size_t mid = (lo + hi) / 2;
        if (iv[mid].first <= p) lo = mid + 1; else hi = mid;
    }
    if (lo == 0) return false;
    return p <= iv[lo - 1].second;   // p within [lo, hi] of the candidate interval
}

std::size_t TreeCover::index_size_bytes() const {
    std::size_t bytes = post_.size() * sizeof(vid_t);
    for (const auto& iv : intervals_) bytes += iv.size() * 2 * sizeof(vid_t);
    return bytes;
}

}  // namespace reachability
