#include "reachability/gripp.hpp"
#include <algorithm>
#include <queue>
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
    // Process hop nodes by ascending order-tree position (Sec. 4.1) and prune against the set U of
    // already-processed hop ranges [start, end] (the four cases of Fig. 4):
    //   (a) h already used as a hop node            -> skip (stamp_)
    //   (b) h's tree instance lies inside some u in U -> RIS(h) subset RIS(u), skip entirely
    //   (c) some u in U lies inside RIS(h)           -> skip that sub-range while scanning
    //   (d) h's tree instance is a sibling of all u  -> no pruning (full scan)
    std::priority_queue<vid_t, std::vector<vid_t>, std::greater<vid_t>> heap;
    std::vector<std::pair<vid_t, vid_t>> U;
    heap.push(tree_inst_[v]); stamp_[v] = qc;
    while (!heap.empty()) {
        vid_t th = heap.top(); heap.pop();
        const vid_t end = ipost_[th];
        bool covered = false;                                  // case (b)
        for (const auto& u : U) if (u.first <= th && th <= u.second) { covered = true; break; }
        if (covered) continue;
        for (vid_t i = th; i <= end;) {
            vid_t jump = -1;                                   // case (c): skip nested processed ranges
            for (const auto& u : U) if (u.first > th && u.first <= i && i <= u.second) jump = std::max(jump, u.second);
            if (jump >= 0) { i = jump + 1; continue; }
            if (inode_[i] == w) return true;
            if (!itree_[i]) {                                  // non-tree instance -> hop node
                vid_t h = inode_[i];
                if (stamp_[h] != qc) { stamp_[h] = qc; heap.push(tree_inst_[h]); }   // case (a) via stamp
            }
            ++i;
        }
        U.push_back({th, end});
    }
    return false;
}

std::size_t GRIPP::index_size_bytes() const {
    return inode_.size() * (2 * sizeof(vid_t) + sizeof(char)) + tree_inst_.size() * sizeof(vid_t);
}

}  // namespace reachability
