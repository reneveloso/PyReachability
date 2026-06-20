#include "reachability/bfl.hpp"
#include <algorithm>
#include <random>

namespace reachability {

namespace {
// Per-vertex hash bit in [0, k*32), drawn in groups (like the reference) so the Bloom filters
// use a controlled number of distinct bits. Correctness is independent of the scheme — the
// bloom is only a necessary-condition filter — so this affects pruning power, not answers.
void make_hash(std::vector<int>& h, vid_t n, int k, std::uint32_t seed) {
    std::mt19937 rng(seed);
    h.assign(n, 0);
    const int bits = k * 32;
    const vid_t group = std::max<vid_t>(1, n / (320 * k));
    vid_t c = group;
    int r = 0;
    for (vid_t v = 0; v < n; ++v) {
        if (c >= group) { c = 0; r = (int)(rng() % (unsigned)bits); }
        ++c;
        h[v] = r;
    }
}
}  // namespace

void BFL::build(const CSRGraph& dag, int k, std::uint32_t seed) {
    dag_ = dag;
    k_ = k;
    n_ = dag_.num_nodes();
    lin_.assign((std::size_t)n_ * k_, 0u);
    lout_.assign((std::size_t)n_ * k_, 0u);
    pre_.assign(n_, 0);
    post_.assign(n_, 0);
    visited_.assign(n_, 0);
    query_cnt_ = 0;

    // reverse CSR (in-neighbours)
    {
        std::vector<vid_t> rs, rd;
        rs.reserve(dag_.num_edges()); rd.reserve(dag_.num_edges());
        for (vid_t u = 0; u < n_; ++u)
            for (const vid_t* it = dag_.out_begin(u); it != dag_.out_end(u); ++it) {
                rs.push_back(*it); rd.push_back(u);
            }
        rdag_ = CSRGraph(n_, rs, rd);
    }

    std::vector<int> hin, hout;
    make_hash(hin, n_, k_, seed);
    make_hash(hout, n_, k_, seed + 1u);

    // Topological order (Kahn) of the DAG.
    std::vector<vid_t> indeg(n_, 0);
    for (vid_t u = 0; u < n_; ++u)
        for (const vid_t* it = dag_.out_begin(u); it != dag_.out_end(u); ++it)
            ++indeg[*it];
    std::vector<vid_t> order;
    order.reserve(n_);
    {
        std::vector<vid_t> ind = indeg, q;
        for (vid_t u = 0; u < n_; ++u) if (ind[u] == 0) q.push_back(u);
        std::size_t head = 0;
        while (head < q.size()) {
            vid_t u = q[head++];
            order.push_back(u);
            for (const vid_t* it = dag_.out_begin(u); it != dag_.out_end(u); ++it)
                if (--ind[*it] == 0) q.push_back(*it);
        }
    }

    // L_in: in topological order, L_in[u] = {hin[u]} ∪ union over in-neighbours.
    for (vid_t u : order) {
        std::uint32_t* lu = &lin_[(std::size_t)u * k_];
        for (const vid_t* it = rdag_.out_begin(u); it != rdag_.out_end(u); ++it) {
            const std::uint32_t* lw = &lin_[(std::size_t)(*it) * k_];
            for (int i = 0; i < k_; ++i) lu[i] |= lw[i];
        }
        lu[hin[u] >> 5] |= 1u << (hin[u] & 31);
    }

    // L_out: in reverse topological order, L_out[u] = {hout[u]} ∪ union over out-neighbours.
    for (std::size_t i = order.size(); i-- > 0;) {
        vid_t u = order[i];
        std::uint32_t* lu = &lout_[(std::size_t)u * k_];
        for (const vid_t* it = dag_.out_begin(u); it != dag_.out_end(u); ++it) {
            const std::uint32_t* lw = &lout_[(std::size_t)(*it) * k_];
            for (int j = 0; j < k_; ++j) lu[j] |= lw[j];
        }
        lu[hout[u] >> 5] |= 1u << (hout[u] & 31);
    }

    // DFS interval over out-edges from the sources (iterative): pre = entry order,
    // post = counter after the subtree.
    {
        std::vector<char> seen(n_, 0);
        vid_t cur = 0;
        struct F { vid_t v; const vid_t* it; const vid_t* end; };
        std::vector<F> st;
        for (vid_t r = 0; r < n_; ++r) {
            if (indeg[r] != 0 || seen[r]) continue;
            seen[r] = 1;
            pre_[r] = cur++;
            st.push_back({r, dag_.out_begin(r), dag_.out_end(r)});
            while (!st.empty()) {
                std::size_t top = st.size() - 1;
                if (st[top].it != st[top].end) {
                    vid_t w = *st[top].it; ++st[top].it;
                    if (!seen[w]) {
                        seen[w] = 1;
                        pre_[w] = cur++;
                        st.push_back({w, dag_.out_begin(w), dag_.out_end(w)});
                    }
                } else {
                    post_[st[top].v] = cur;
                    st.pop_back();
                }
            }
        }
    }
}

int BFL::cut(vid_t u, vid_t v) const {
    if (post_[u] < post_[v]) return -1;          // interval negative cut
    if (pre_[u] <= pre_[v]) return 1;            // interval positive cut (tree path)
    const std::uint32_t* ou = &lout_[(std::size_t)u * k_];
    const std::uint32_t* ov = &lout_[(std::size_t)v * k_];
    for (int i = 0; i < k_; ++i)                  // L_out[v] must be subset of L_out[u]
        if ((ou[i] & ov[i]) != ov[i]) return -1;
    const std::uint32_t* iu = &lin_[(std::size_t)u * k_];
    const std::uint32_t* iv = &lin_[(std::size_t)v * k_];
    for (int i = 0; i < k_; ++i)                  // L_in[u] must be subset of L_in[v]
        if ((iu[i] & iv[i]) != iu[i]) return -1;
    return 0;
}

bool BFL::reaches(vid_t u, vid_t v) {
    if (u == v) return true;
    int r = cut(u, v);
    if (r) return r == 1;

    ++query_cnt_;
    std::vector<vid_t> stack;
    visited_[u] = query_cnt_;
    stack.push_back(u);
    while (!stack.empty()) {
        vid_t x = stack.back(); stack.pop_back();
        for (const vid_t* it = dag_.out_begin(x); it != dag_.out_end(x); ++it) {
            vid_t w = *it;
            if (w == v) return true;
            if (visited_[w] == query_cnt_) continue;
            int rw = cut(w, v);
            if (rw == 1) return true;
            if (rw == 0) { visited_[w] = query_cnt_; stack.push_back(w); }
        }
    }
    return false;
}

std::size_t BFL::index_size_bytes() const {
    return (lin_.size() + lout_.size()) * sizeof(std::uint32_t) +
           (pre_.size() + post_.size()) * sizeof(vid_t);
}

}  // namespace reachability
