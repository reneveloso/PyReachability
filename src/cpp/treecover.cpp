#include "reachability/treecover.hpp"
#include <algorithm>

namespace reachability {

void TreeCover::build(const CSRGraph& dag) {
    n_ = dag.num_nodes();
    post_.assign(n_, 0);
    intervals_.assign(n_, {});

    // DFS spanning forest from the in-degree-0 roots; record post-order (finish) numbers and
    // the finish sequence. Post-order is a reverse topological order: every successor of v
    // (tree or non-tree, in a DAG) finishes before v.
    std::vector<vid_t> indeg(n_, 0);
    for (vid_t u = 0; u < n_; ++u)
        for (const vid_t* it = dag.out_begin(u); it != dag.out_end(u); ++it)
            ++indeg[*it];
    std::vector<char> seen(n_, 0);
    std::vector<vid_t> finish;
    finish.reserve(n_);
    {
        struct F { vid_t v; const vid_t* it; const vid_t* end; };
        std::vector<F> st;
        vid_t counter = 0;
        for (vid_t r = 0; r < n_; ++r) {
            if (indeg[r] != 0 || seen[r]) continue;
            seen[r] = 1;
            st.push_back({r, dag.out_begin(r), dag.out_end(r)});
            while (!st.empty()) {
                std::size_t top = st.size() - 1;
                if (st[top].it != st[top].end) {
                    vid_t w = *st[top].it; ++st[top].it;
                    if (!seen[w]) { seen[w] = 1; st.push_back({w, dag.out_begin(w), dag.out_end(w)}); }
                } else {
                    post_[st[top].v] = counter++;
                    finish.push_back(st[top].v);
                    st.pop_back();
                }
            }
        }
    }

    // Build reachable-post-order interval sets in finish order (successors first).
    // I[v] = merge( {[post[v],post[v]]} U over successors w: I[w] ).
    std::vector<std::pair<vid_t, vid_t>> buf;
    for (vid_t v : finish) {
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
