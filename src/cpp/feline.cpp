#include "reachability/feline.hpp"
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
}

// Algorithm 2: dominance negative cut + dominance-pruned guided DFS.
bool Feline::reaches(vid_t u, vid_t v) {
    if (u == v) return true;
    if (!dominates(u, v)) return false;      // negative cut (contrapositive of Theorem 1)

    ++query_cnt_;
    std::vector<vid_t> stack;
    visited_[u] = query_cnt_;
    stack.push_back(u);
    while (!stack.empty()) {
        vid_t x = stack.back(); stack.pop_back();
        for (const vid_t* it = dag_.out_begin(x); it != dag_.out_end(x); ++it) {
            vid_t w = *it;
            if (w == v) return true;
            // expand only neighbors still able to dominate v (others cannot reach v)
            if (visited_[w] != query_cnt_ && dominates(w, v)) {
                visited_[w] = query_cnt_;
                stack.push_back(w);
            }
        }
    }
    return false;
}

std::size_t Feline::index_size_bytes() const {
    return (X_.size() + Y_.size()) * sizeof(vid_t);
}

}  // namespace reachability
