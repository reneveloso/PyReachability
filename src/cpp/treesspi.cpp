#include "reachability/treesspi.hpp"
#include "reachability/optimal_tree.hpp"
#include <algorithm>
#include <vector>

namespace reachability {

void TreeSSPI::build(const CSRGraph& dag) {
    n_ = dag.num_nodes();
    parent_.assign(n_, -1); pre_.assign(n_, 0); a_.assign(n_, 0); b_.assign(n_, 0);
    pl_.assign(n_, {});
    stamp_.assign(n_, 0); query_cnt_ = 0;
    if (n_ == 0) return;

    // Agrawal's optimum tree cover, then preorder numbering + subtree sizes over that tree.
    parent_ = optimal_tree_parent(dag);
    std::vector<std::vector<vid_t>> children(n_);
    for (vid_t v = 0; v < n_; ++v) if (parent_[v] != -1) children[parent_[v]].push_back(v);
    std::vector<vid_t> size(n_, 1);
    {
        vid_t counter = 0;
        struct F { vid_t v; std::size_t ci; };
        std::vector<F> st;
        for (vid_t r = 0; r < n_; ++r) {
            if (parent_[r] != -1) continue;
            pre_[r] = counter++; st.push_back({r, 0});
            while (!st.empty()) {
                F& f = st.back();
                if (f.ci < children[f.v].size()) { vid_t c = children[f.v][f.ci++]; pre_[c] = counter++; st.push_back({c, 0}); }
                else { if (parent_[f.v] != -1) size[parent_[f.v]] += size[f.v]; st.pop_back(); }
            }
        }
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
