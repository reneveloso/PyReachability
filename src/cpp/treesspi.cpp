#include "reachability/treesspi.hpp"
#include <algorithm>
#include <vector>

namespace reachability {

void TreeSSPI::build(const CSRGraph& dag) {
    n_ = dag.num_nodes();
    parent_.assign(n_, -1); pre_.assign(n_, 0); a_.assign(n_, 0); b_.assign(n_, 0);
    pl_.assign(n_, {});
    stamp_.assign(n_, 0); query_cnt_ = 0;
    if (n_ == 0) return;

    // roots = in-degree 0 (deterministic spanning-forest seeds)
    std::vector<vid_t> indeg(n_, 0);
    for (vid_t u = 0; u < n_; ++u)
        for (const vid_t* it = dag.out_begin(u); it != dag.out_end(u); ++it) ++indeg[*it];

    // DFS spanning forest + preorder numbering + subtree sizes
    std::vector<vid_t> size(n_, 1);
    std::vector<char> seen(n_, 0);
    {
        vid_t counter = 0;
        struct F { vid_t v; const vid_t* it; const vid_t* end; };
        std::vector<F> st;
        auto run = [&](vid_t r) {
            if (seen[r]) return;
            seen[r] = 1; pre_[r] = counter++;
            st.push_back({r, dag.out_begin(r), dag.out_end(r)});
            while (!st.empty()) {
                F& f = st.back();
                if (f.it != f.end) {
                    vid_t w = *f.it; ++f.it;
                    if (!seen[w]) { seen[w] = 1; parent_[w] = f.v; pre_[w] = counter++;
                                    st.push_back({w, dag.out_begin(w), dag.out_end(w)}); }
                } else {
                    if (parent_[f.v] != -1) size[parent_[f.v]] += size[f.v];
                    st.pop_back();
                }
            }
        };
        for (vid_t r = 0; r < n_; ++r) if (indeg[r] == 0) run(r);
        for (vid_t r = 0; r < n_; ++r) run(r);
    }
    for (vid_t v = 0; v < n_; ++v) { a_[v] = pre_[v]; b_[v] = pre_[v] + size[v]; }

    // SSPI: for each non-tree edge (u,w), store u in PL(w); drop superfluous (u already tree-reaches w)
    for (vid_t u = 0; u < n_; ++u)
        for (const vid_t* it = dag.out_begin(u); it != dag.out_end(u); ++it) {
            vid_t w = *it;
            if (parent_[w] == u) continue;        // tree edge
            if (anc(u, w)) continue;              // superfluous: tail already tree-reaches head
            pl_[w].push_back(u);
        }
    for (vid_t w = 0; w < n_; ++w)                // sort by start interval (paper's order)
        std::sort(pl_[w].begin(), pl_[w].end(), [&](vid_t p, vid_t q){ return pre_[p] < pre_[q]; });
}

bool TreeSSPI::reaches(vid_t x, vid_t y) {
    if (x == y) return true;
    if (anc(x, y)) return true;                   // tree (ppure) reachability

    // guided SSPI search: explore nodes known to reach y; their predecessors (own + inherited
    // along tree ancestors) also reach y. x reaches y iff x tree-reaches one of them.
    ++query_cnt_;
    const int qc = query_cnt_;
    std::vector<vid_t> st;
    st.push_back(y); stamp_[y] = qc;
    while (!st.empty()) {
        vid_t w = st.back(); st.pop_back();
        for (vid_t z = w; z != -1; z = parent_[z])    // w and its tree ancestors (inheritance)
            for (vid_t u : pl_[z]) {
                if (anc(x, u)) return true;           // x tree-reaches u, u -> ... -> y
                if (stamp_[u] != qc) { stamp_[u] = qc; st.push_back(u); }
            }
    }
    return false;
}

std::size_t TreeSSPI::index_size_bytes() const {
    std::size_t b = (parent_.size() + pre_.size() + a_.size() + b_.size()) * sizeof(vid_t);
    for (const auto& p : pl_) b += p.size() * sizeof(vid_t);
    return b;
}

}  // namespace reachability
