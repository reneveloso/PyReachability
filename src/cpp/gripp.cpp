#include "reachability/gripp.hpp"
#include <vector>

namespace reachability {

void GRIPP::build(const CSRGraph& dag) {
    n_ = dag.num_nodes();
    inode_.clear(); ipost_.clear(); itree_.clear();
    tree_inst_.assign(n_, -1);
    stamp_.assign(n_, 0); query_cnt_ = 0;
    if (n_ == 0) return;

    // in-degree-0 roots first, for a deterministic order tree
    std::vector<vid_t> indeg(n_, 0);
    for (vid_t u = 0; u < n_; ++u)
        for (const vid_t* it = dag.out_begin(u); it != dag.out_end(u); ++it) ++indeg[*it];

    // DFS builds the order tree: instance ids are assigned in preorder; tree instances recurse,
    // non-tree instances are leaves. ipost[t] = last preorder id in t's subtree.
    inode_.reserve(dag.num_edges() + n_);
    ipost_.reserve(dag.num_edges() + n_);
    itree_.reserve(dag.num_edges() + n_);
    struct F { vid_t inst; const vid_t* it; const vid_t* end; };
    std::vector<F> st;
    auto new_inst = [&](vid_t node, char tree) -> vid_t {
        vid_t id = (vid_t)inode_.size();
        inode_.push_back(node); ipost_.push_back(id); itree_.push_back(tree);
        return id;
    };
    auto run = [&](vid_t r) {
        if (tree_inst_[r] != -1) return;
        vid_t id = new_inst(r, 1); tree_inst_[r] = id;
        st.push_back({id, dag.out_begin(r), dag.out_end(r)});
        while (!st.empty()) {
            F& f = st.back();
            if (f.it != f.end) {
                vid_t w = *f.it; ++f.it;
                if (tree_inst_[w] == -1) {
                    vid_t wid = new_inst(w, 1); tree_inst_[w] = wid;
                    st.push_back({wid, dag.out_begin(w), dag.out_end(w)});
                } else {
                    new_inst(w, 0);              // non-tree leaf instance (ipost = its own id)
                }
            } else {
                ipost_[f.inst] = (vid_t)inode_.size() - 1;   // subtree end
                st.pop_back();
            }
        }
    };
    for (vid_t r = 0; r < n_; ++r) if (indeg[r] == 0) run(r);
    for (vid_t r = 0; r < n_; ++r) run(r);
}

bool GRIPP::reaches(vid_t v, vid_t w) {
    if (v == w) return true;
    ++query_cnt_;
    const int qc = query_cnt_;
    std::vector<vid_t> st;
    st.push_back(tree_inst_[v]); stamp_[v] = qc;
    while (!st.empty()) {
        vid_t t = st.back(); st.pop_back();
        const vid_t end = ipost_[t];
        for (vid_t i = t; i <= end; ++i) {       // RIS(v): instances in the subtree
            if (inode_[i] == w) return true;
            if (!itree_[i]) {                    // non-tree instance -> hop node
                vid_t h = inode_[i];
                if (stamp_[h] != qc) { stamp_[h] = qc; st.push_back(tree_inst_[h]); }
            }
        }
    }
    return false;
}

std::size_t GRIPP::index_size_bytes() const {
    return inode_.size() * (2 * sizeof(vid_t) + sizeof(char)) + tree_inst_.size() * sizeof(vid_t);
}

}  // namespace reachability
