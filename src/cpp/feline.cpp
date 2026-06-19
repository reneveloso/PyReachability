#include "reachability/feline.hpp"
#include "reachability/levels.hpp"
#include <algorithm>
#include <queue>
#include <utility>

namespace reachability {

// Algorithm 1: two topological orderings.
//   X = a plain topological order (Kahn, FIFO).
//   Y = Kahn where, among the current roots, we always pop the one with the largest X
//       (Kornaropoulos heuristic — locally minimizes false-implied paths).
void Feline::build(const CSRGraph& dag) {
    dag_ = dag;
    n_ = dag_.num_nodes();
    X_.assign(n_, 0);
    Y_.assign(n_, 0);
    visited_.assign(n_, 0);
    query_cnt_ = 0;

    std::vector<vid_t> indeg(n_, 0);
    for (vid_t u = 0; u < n_; ++u)
        for (const vid_t* it = dag_.out_begin(u); it != dag_.out_end(u); ++it)
            ++indeg[*it];

    // X: FIFO Kahn.
    {
        std::vector<vid_t> ind = indeg;
        std::vector<vid_t> q;
        q.reserve(n_);
        for (vid_t u = 0; u < n_; ++u) if (ind[u] == 0) q.push_back(u);
        std::size_t head = 0;
        vid_t rank = 0;
        while (head < q.size()) {
            vid_t u = q[head++];
            X_[u] = rank++;
            for (const vid_t* it = dag_.out_begin(u); it != dag_.out_end(u); ++it)
                if (--ind[*it] == 0) q.push_back(*it);
        }
    }

    // Y: Kahn with a max-heap on X (pop the available root of highest X rank).
    {
        std::vector<vid_t> ind = indeg;
        std::priority_queue<std::pair<vid_t, vid_t>> pq;   // (X[u], u), max-heap by X
        for (vid_t u = 0; u < n_; ++u)
            if (ind[u] == 0) pq.push({X_[u], u});
        vid_t rank = 0;
        while (!pq.empty()) {
            vid_t u = pq.top().second; pq.pop();
            Y_[u] = rank++;
            for (const vid_t* it = dag_.out_begin(u); it != dag_.out_end(u); ++it)
                if (--ind[*it] == 0) pq.push({X_[*it], *it});
        }
    }

    level_ = topological_levels(dag_);   // shared level filter (negative cut + DFS prune)
    compute_positive_cut();
}

// Min-post intervals over a spanning forest (rooted at the in-degree-0 vertices). For each
// vertex: pe = post-order finish number; ps = minimum pe over its TREE subtree only (no
// non-tree edges), so [ps, pe] contains exactly the vertex's tree-descendants. Iterative DFS.
void Feline::compute_positive_cut() {
    ps_.assign(n_, 0);
    pe_.assign(n_, 0);
    std::vector<vid_t> indeg(n_, 0);
    for (vid_t u = 0; u < n_; ++u)
        for (const vid_t* it = dag_.out_begin(u); it != dag_.out_end(u); ++it)
            ++indeg[*it];
    std::vector<char> seen(n_, 0);
    vid_t counter = 0;
    const vid_t INF = n_ + 1;
    struct Frame { vid_t v; const vid_t* it; const vid_t* end; vid_t curmin; };
    std::vector<Frame> st;
    for (vid_t r = 0; r < n_; ++r) {
        if (indeg[r] != 0 || seen[r]) continue;
        seen[r] = 1;
        st.push_back({r, dag_.out_begin(r), dag_.out_end(r), INF});
        while (!st.empty()) {
            std::size_t top = st.size() - 1;     // re-index: push() may reallocate
            if (st[top].it != st[top].end) {
                vid_t w = *st[top].it; ++st[top].it;
                if (!seen[w]) {                  // tree edge: descend
                    seen[w] = 1;
                    st.push_back({w, dag_.out_begin(w), dag_.out_end(w), INF});
                }
                // non-tree edge: ignored (positive cut spans tree descendants only)
            } else {
                vid_t v = st[top].v, cm = st[top].curmin;
                ++counter;
                vid_t s = std::min(cm, counter);
                ps_[v] = s; pe_[v] = counter;
                st.pop_back();
                if (!st.empty()) st.back().curmin = std::min(st.back().curmin, s);
            }
        }
    }
}

// Algorithm 2: dominance negative cut + dominance-pruned guided DFS.
bool Feline::reaches(vid_t u, vid_t v) {
    if (u == v) return true;
    if (positive_contains(u, v)) return true;   // positive cut (tree path) — exact positive
    if (level_[u] >= level_[v]) return false;   // level filter (exact negative)
    if (!dominates(u, v)) return false;         // dominance negative cut (Theorem 1)

    const vid_t lv = level_[v];
    ++query_cnt_;
    std::vector<vid_t> stack;
    visited_[u] = query_cnt_;
    stack.push_back(u);
    while (!stack.empty()) {
        vid_t x = stack.back(); stack.pop_back();
        for (const vid_t* it = dag_.out_begin(x); it != dag_.out_end(x); ++it) {
            vid_t w = *it;
            if (w == v) return true;
            // expand only neighbors that still dominate v and sit below its level
            if (visited_[w] != query_cnt_ && level_[w] < lv && dominates(w, v)) {
                if (positive_contains(w, v)) return true;   // positive short-circuit
                visited_[w] = query_cnt_;
                stack.push_back(w);
            }
        }
    }
    return false;
}

std::size_t Feline::index_size_bytes() const {
    return (X_.size() + Y_.size() + level_.size() + ps_.size() + pe_.size()) * sizeof(vid_t);
}

}  // namespace reachability
