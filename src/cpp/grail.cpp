#include "reachability/grail.hpp"
#include <random>
#include <algorithm>

namespace reachability {

void Grail::build(const CSRGraph& dag, int d, std::uint32_t seed) {
    dag_ = dag;
    d_ = d;
    n_ = dag_.num_nodes();
    pre_.assign((std::size_t)d_ * n_, 0);
    post_.assign((std::size_t)d_ * n_, 0);
    middle_.assign((std::size_t)d_ * n_, 0);
    visited_.assign(n_, 0);
    query_cnt_ = 0;
    for (int k = 0; k < d_; ++k)
        label_dimension(k, seed + (std::uint32_t)k);
}

// One randomized post-order DFS labeling, written iteratively.
void Grail::label_dimension(int k, std::uint32_t seed) {
    std::mt19937 rng(seed);

    // roots = in-degree 0 (CSR stores out-edges, so count in-degrees by scanning).
    std::vector<vid_t> indeg(n_, 0);
    for (vid_t u = 0; u < n_; ++u)
        for (const vid_t* it = dag_.out_begin(u); it != dag_.out_end(u); ++it)
            ++indeg[*it];
    std::vector<vid_t> roots;
    for (vid_t u = 0; u < n_; ++u) if (indeg[u] == 0) roots.push_back(u);
    std::shuffle(roots.begin(), roots.end(), rng);

    std::vector<char> seen(n_, 0);
    vid_t counter = 0;
    const vid_t INF = n_ + 1;

    // Explicit DFS frames: vertex, its (shuffled) neighbors, cursor, running subtree min.
    struct Frame { vid_t v; std::vector<vid_t> nbrs; std::size_t idx; vid_t curmin; };
    std::vector<Frame> stack;

    auto push = [&](vid_t v) {
        seen[v] = 1;
        // middle = finish-counter at entry; (middle, post] are v's tree-descendants,
        // which gives an exact positive cut in contains_pp().
        middle_[(std::size_t)v * d_ + k] = counter;
        std::vector<vid_t> nbrs(dag_.out_begin(v), dag_.out_end(v));
        std::shuffle(nbrs.begin(), nbrs.end(), rng);   // random child order
        stack.push_back(Frame{v, std::move(nbrs), 0, INF});
    };

    for (vid_t r : roots) {
        if (seen[r]) continue;
        push(r);
        while (!stack.empty()) {
            std::size_t top = stack.size() - 1;       // re-index each turn: push() may realloc
            if (stack[top].idx < stack[top].nbrs.size()) {
                vid_t w = stack[top].nbrs[stack[top].idx++];
                if (!seen[w]) {
                    push(w);                          // descend (tree edge)
                } else {
                    // forward/cross edge: child already labeled — pull its min up
                    stack[top].curmin = std::min(stack[top].curmin,
                                                 pre_[(std::size_t)w * d_ + k]);
                }
            } else {
                // finish v: assign post = finish number, pre = subtree min
                vid_t v = stack[top].v;
                vid_t cm = stack[top].curmin;
                ++counter;
                vid_t pv = std::min(cm, counter);
                pre_[(std::size_t)v * d_ + k] = pv;
                post_[(std::size_t)v * d_ + k] = counter;
                stack.pop_back();
                if (!stack.empty())
                    stack.back().curmin = std::min(stack.back().curmin, pv);
            }
        }
    }
}

bool Grail::contains(vid_t u, vid_t v) const {
    for (int k = 0; k < d_; ++k) {
        if (pre_[(std::size_t)u * d_ + k] > pre_[(std::size_t)v * d_ + k]) return false;
        if (post_[(std::size_t)u * d_ + k] < post_[(std::size_t)v * d_ + k]) return false;
    }
    return true;
}

int Grail::contains_pp(vid_t u, vid_t v) const {
    for (int k = 0; k < d_; ++k) {
        std::size_t iu = (std::size_t)u * d_ + k, iv = (std::size_t)v * d_ + k;
        if (pre_[iu] > pre_[iv]) return -1;          // exact negative cut
        if (post_[iu] < post_[iv]) return -1;        // exact negative cut
        if (middle_[iu] < post_[iv]) return 1;       // exact positive cut (tree-descendant)
    }
    return 0;                                        // inconclusive
}

bool Grail::reaches(vid_t u, vid_t v) {
    if (u == v) return true;                 // reflexive
    int r = contains_pp(u, v);
    if (r == -1) return false;               // exact negative
    if (r == 1) return true;                 // exact positive

    // Inconclusive: guided DFS, using the PP cuts at every neighbor.
    ++query_cnt_;
    std::vector<vid_t> stack;
    visited_[u] = query_cnt_;
    stack.push_back(u);
    while (!stack.empty()) {
        vid_t x = stack.back(); stack.pop_back();
        for (const vid_t* it = dag_.out_begin(x); it != dag_.out_end(x); ++it) {
            vid_t w = *it;
            if (visited_[w] == query_cnt_) continue;
            int rw = contains_pp(w, v);
            if (rw == 1) return true;        // positive cut: w (hence x) reaches v
            if (rw == 0) {                   // inconclusive: descend
                visited_[w] = query_cnt_;
                stack.push_back(w);
            }
            // rw == -1: prune this branch
        }
    }
    return false;
}

std::size_t Grail::index_size_bytes() const {
    return (pre_.size() + post_.size() + middle_.size()) * sizeof(vid_t);
}

}  // namespace reachability
