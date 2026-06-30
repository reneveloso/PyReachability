#include "reachability/dual.hpp"
#include <algorithm>
#include <cstdint>
#include <unordered_set>
#include <vector>

namespace reachability {

void DualLabeling::build(const CSRGraph& dag) {
    n_ = dag.num_nodes();
    pre_.assign(n_, 0); a_.assign(n_, 0); b_.assign(n_, 0);
    tlc_.clear();
    if (n_ == 0) return;

    // Section 5: reduce G to its minimal equivalent graph (the unique transitive reduction of a
    // DAG) so the spanning tree leaves as few non-tree edges t as possible. Topological order:
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
    // descendant bitsets reach[u] = {u} U successors' (reverse topo)
    const vid_t W = (n_ + 63) / 64;
    std::vector<std::uint64_t> reach((std::size_t)n_ * W, 0);
    auto rget = [&](vid_t u, vid_t b){ return (reach[(std::size_t)u * W + (b >> 6)] >> (b & 63)) & 1ULL; };
    for (std::size_t i = topo.size(); i-- > 0;) {
        vid_t u = topo[i]; reach[(std::size_t)u * W + (u >> 6)] |= (std::uint64_t)1 << (u & 63);
        for (const vid_t* it = dag.out_begin(u); it != dag.out_end(u); ++it) {
            std::uint64_t* ru = &reach[(std::size_t)u * W]; const std::uint64_t* rw = &reach[(std::size_t)(*it) * W];
            for (vid_t k = 0; k < W; ++k) ru[k] |= rw[k];
        }
    }
    // minimal equivalent graph: keep edge (u,v) iff no other out-neighbour w of u also reaches v
    std::vector<std::vector<vid_t>> redOut(n_);
    for (vid_t u = 0; u < n_; ++u)
        for (const vid_t* it = dag.out_begin(u); it != dag.out_end(u); ++it) {
            vid_t v = *it; bool redundant = false;
            for (const vid_t* jt = dag.out_begin(u); jt != dag.out_end(u); ++jt)
                if (*jt != v && rget(*jt, v)) { redundant = true; break; }
            if (!redundant) redOut[u].push_back(v);
        }

    // DFS spanning forest over the minimal equivalent graph; preorder + subtree sizes
    std::vector<vid_t> parent(n_, -1), size(n_, 1);
    std::vector<char> seen(n_, 0);
    {
        vid_t counter = 0;
        struct F { vid_t v; std::size_t ci; };
        std::vector<F> st;
        auto visit_root = [&](vid_t r) {
            if (seen[r]) return;
            seen[r] = 1; pre_[r] = counter++; st.push_back({r, 0});
            while (!st.empty()) {
                F& f = st.back();
                if (f.ci < redOut[f.v].size()) { vid_t w = redOut[f.v][f.ci++];
                    if (!seen[w]) { seen[w] = 1; parent[w] = f.v; pre_[w] = counter++; st.push_back({w, 0}); } }
                else { if (parent[f.v] != -1) size[parent[f.v]] += size[f.v]; st.pop_back(); }
            }
        };
        for (vid_t r = 0; r < n_; ++r) if (indeg[r] == 0) visit_root(r);
        for (vid_t r = 0; r < n_; ++r) visit_root(r);
    }
    for (vid_t v = 0; v < n_; ++v) { a_[v] = pre_[v]; b_[v] = pre_[v] + size[v]; }
    auto desc = [&](vid_t u, vid_t w)->bool { return a_[u] <= pre_[w] && pre_[w] < b_[u]; };

    // non-tree edges (of the minimal equivalent graph) -> initial links i -> [j, k)
    std::vector<Link> links;
    for (vid_t u = 0; u < n_; ++u)
        for (vid_t v : redOut[u]) {
            if (parent[v] == u) continue;        // tree edge
            if (desc(u, v)) continue;            // superfluous (v already tree-reachable from u)
            links.push_back({a_[u], a_[v], b_[v]});
        }

    // transitive closure of the link table (compose i1->[j1,k1), i2->[j2,k2) when i2 in [j1,k1))
    const long long M = (long long)n_ + 1;
    auto code = [&](const Link& l)->long long { return (l.i * M + l.j) * M + l.k; };
    std::unordered_set<long long> seenl;
    std::vector<Link> all;
    std::vector<Link> queue;
    for (const Link& l : links) if (seenl.insert(code(l)).second) { all.push_back(l); queue.push_back(l); }
    std::size_t qh = 0;
    while (qh < queue.size()) {
        Link l1 = queue[qh++];
        const std::size_t cur = all.size();   // snapshot to pair l1 with existing links
        for (std::size_t z = 0; z < cur; ++z) {
            Link l2 = all[z];
            if (l1.j <= l2.i && l2.i < l1.k) {                 // l1 then l2
                Link nl{l1.i, l2.j, l2.k};
                if (seenl.insert(code(nl)).second) { all.push_back(nl); queue.push_back(nl); }
            }
            if (l2.j <= l1.i && l1.i < l2.k) {                 // l2 then l1
                Link nl{l2.i, l1.j, l1.k};
                if (seenl.insert(code(nl)).second) { all.push_back(nl); queue.push_back(nl); }
            }
        }
    }
    tlc_.swap(all);
}

bool DualLabeling::query(vid_t u, vid_t v) const {
    if (u == v) return true;
    const vid_t c = pre_[v];
    if (a_[u] <= c && c < b_[u]) return true;                 // tree reachability
    for (const Link& l : tlc_)                                 // Theorem 1: non-tree reachability
        if (a_[u] <= l.i && l.i < b_[u] && l.j <= c && c < l.k) return true;
    return false;
}

std::size_t DualLabeling::index_size_bytes() const {
    return (pre_.size() + a_.size() + b_.size()) * sizeof(vid_t) + tlc_.size() * sizeof(Link);
}

}  // namespace reachability
