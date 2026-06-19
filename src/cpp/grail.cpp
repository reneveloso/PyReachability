#include "reachability/grail.hpp"
#include "reachability/levels.hpp"
#include <random>
#include <algorithm>

namespace reachability {

void Grail::build(const CSRGraph& dag, int d, std::uint32_t seed, bool bidirectional) {
    dag_ = dag;
    bidirectional_ = bidirectional;
    d_ = d;
    n_ = dag_.num_nodes();
    pre_.assign((std::size_t)d_ * n_, 0);
    post_.assign((std::size_t)d_ * n_, 0);
    middle_.assign((std::size_t)d_ * n_, 0);
    visited_.assign(n_, 0);
    query_cnt_ = 0;
    for (int k = 0; k < d_; ++k)
        label_dimension(k, seed + (std::uint32_t)k);
    top_level_ = topological_levels(dag_);

    if (bidirectional_) {
        // Reverse CSR (in-edges) for the backward half of the bidirectional search.
        std::vector<vid_t> rs, rd;
        rs.reserve(dag_.num_edges());
        rd.reserve(dag_.num_edges());
        for (vid_t u = 0; u < n_; ++u)
            for (const vid_t* it = dag_.out_begin(u); it != dag_.out_end(u); ++it) {
                rs.push_back(*it); rd.push_back(u);
            }
        rdag_ = CSRGraph(n_, rs, rd);
    }
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
    if (top_level_[u] >= top_level_[v]) return false;   // level filter (exact negative)
    int r = contains_pp(u, v);
    if (r == -1) return false;               // exact negative
    if (r == 1) return true;                 // exact positive
    // Inconclusive: fall back to a search (one- or two-sided).
    return bidirectional_ ? reaches_bidirectional(u, v) : reaches_guided(u, v);
}

// One-sided guided DFS from u, pruned by the PP cuts and the level filter.
bool Grail::reaches_guided(vid_t u, vid_t v) {
    const vid_t lv = top_level_[v];
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
            // rw == 0 here implies w != v, so the level prune cannot skip the target.
            if (rw == 0 && top_level_[w] < lv) {
                visited_[w] = query_cnt_;
                stack.push_back(w);
            }
            // rw == -1, or level too high: prune this branch
        }
    }
    return false;
}

// Two-sided search: a forward frontier from u (reachable-from-u) and a backward
// frontier from v (can-reach-v) grow alternately; success when they meet. Both
// sides are pruned by the PP cuts and the level filter. Forward stamps use +qc,
// backward stamps use -qc, so a node carrying the other side's stamp is a meet.
bool Grail::reaches_bidirectional(vid_t u, vid_t v) {
    ++query_cnt_;
    const int F = query_cnt_, B = -query_cnt_;
    const vid_t lu = top_level_[u], lv = top_level_[v];
    std::vector<vid_t> fq, bq;
    std::size_t fh = 0, bh = 0;
    visited_[u] = F; fq.push_back(u);
    visited_[v] = B; bq.push_back(v);
    while (fh < fq.size() && bh < bq.size()) {
        // forward: expand one reachable-from-u node toward v
        vid_t x = fq[fh++];
        if (top_level_[x] < lv) {                 // x can still reach v
            for (const vid_t* it = dag_.out_begin(x); it != dag_.out_end(x); ++it) {
                vid_t w = *it;
                if (visited_[w] == B) return true;        // met the backward frontier
                if (visited_[w] == F) continue;
                int rw = contains_pp(w, v);
                if (rw == 1) return true;
                if (rw == 0) { visited_[w] = F; fq.push_back(w); }
            }
        }
        // backward: expand one can-reach-v node toward u (over in-edges)
        vid_t y = bq[bh++];
        if (lu < top_level_[y]) {                 // u can still reach y
            for (const vid_t* it = rdag_.out_begin(y); it != rdag_.out_end(y); ++it) {
                vid_t w = *it;
                if (visited_[w] == F) return true;        // met the forward frontier
                if (visited_[w] == B) continue;
                int rw = contains_pp(u, w);
                if (rw == 1) return true;
                if (rw == 0) { visited_[w] = B; bq.push_back(w); }
            }
        }
    }
    return false;
}

std::size_t Grail::index_size_bytes() const {
    std::size_t bytes =
        (pre_.size() + post_.size() + middle_.size() + top_level_.size()) * sizeof(vid_t);
    if (bidirectional_)
        bytes += rdag_.num_edges() * sizeof(vid_t) + (std::size_t)(n_ + 1) * sizeof(std::size_t);
    return bytes;
}

}  // namespace reachability
