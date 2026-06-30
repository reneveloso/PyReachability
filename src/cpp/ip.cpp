#include "reachability/ip.hpp"
#include "reachability/levels.hpp"
#include <algorithm>
#include <numeric>
#include <random>
#include <vector>

namespace reachability {

namespace {
// keep the k smallest distinct values from `cands` in `dst` (sorted ascending)
void keep_topk(std::vector<vid_t>& dst, std::vector<vid_t>& cands, int k) {
    std::sort(cands.begin(), cands.end());
    cands.erase(std::unique(cands.begin(), cands.end()), cands.end());
    if ((int)cands.size() > k) cands.resize(k);
    dst = cands;
}
}  // namespace

void IP::build(const CSRGraph& dag, int k, int np, int h, int mu, unsigned seed) {
    n_ = dag.num_nodes();
    k_ = k < 1 ? 1 : k;
    np_ = np < 1 ? 1 : np;
    h_ = h < 0 ? 0 : h;
    mu_ = mu < 0 ? 0 : mu;
    fwd_ = dag;
    level_ = topological_levels(dag);
    lout_.assign((std::size_t)np_ * n_, {});
    lin_.assign((std::size_t)np_ * n_, {});
    lhv_.assign(n_, {});
    outdeg_.assign(n_, 0);
    stamp_.assign(n_, 0); query_cnt_ = 0;
    if (n_ == 0) return;

    // topological order (Kahn) + reverse graph
    std::vector<vid_t> indeg(n_, 0), rs, rd;
    rs.reserve(dag.num_edges()); rd.reserve(dag.num_edges());
    for (vid_t u = 0; u < n_; ++u)
        for (const vid_t* it = dag.out_begin(u); it != dag.out_end(u); ++it) { ++indeg[*it]; rs.push_back(*it); rd.push_back(u); }
    CSRGraph rev(n_, rs, rd);
    ldown_ = topological_levels(rev);                 // backward topological level (Ldown)
    for (vid_t u = 0; u < n_; ++u) outdeg_[u] = (vid_t)(dag.out_end(u) - dag.out_begin(u));
    std::vector<vid_t> topo; topo.reserve(n_);
    {
        std::vector<vid_t> ind = indeg, q;
        for (vid_t u = 0; u < n_; ++u) if (ind[u] == 0) q.push_back(u);
        std::size_t hh = 0;
        while (hh < q.size()) { vid_t u = q[hh++]; topo.push_back(u);
            for (const vid_t* it = dag.out_begin(u); it != dag.out_end(u); ++it)
                if (--ind[*it] == 0) q.push_back(*it); }
    }

    // HV-Label (Algorithm 3): Lhv(u) = up to h largest-out-degree huge vertices (out-degree > mu)
    // that reach u, propagated along in-neighbours in topological order.
    if (h_ > 0) {
        for (vid_t u = 0; u < n_; ++u) if (outdeg_[u] > (vid_t)mu_) lhv_[u].push_back(u);
        std::vector<vid_t> tmp;
        for (vid_t u : topo) {
            for (const vid_t* it = rev.out_begin(u); it != rev.out_end(u); ++it) {   // in-neighbours
                const std::vector<vid_t>& w = lhv_[*it];
                if (w.empty()) continue;
                tmp.clear();                              // union (both sorted by id), dedup
                std::set_union(lhv_[u].begin(), lhv_[u].end(), w.begin(), w.end(), std::back_inserter(tmp));
                if ((int)tmp.size() > h_) {               // keep the h largest by out-degree
                    std::nth_element(tmp.begin(), tmp.begin() + h_, tmp.end(),
                                     [&](vid_t a, vid_t b){ return outdeg_[a] > outdeg_[b]; });
                    tmp.resize(h_);
                    std::sort(tmp.begin(), tmp.end());    // restore id order for membership tests
                }
                lhv_[u].swap(tmp);
            }
        }
    }

    for (int p = 0; p < np_; ++p) {
        // random permutation pi of [0, n)
        std::vector<vid_t> pi(n_);
        std::iota(pi.begin(), pi.end(), 0);
        std::mt19937 rng(seed + 7919u * (unsigned)p);
        std::shuffle(pi.begin(), pi.end(), rng);

        // Out labels: reverse topo, mink over {pi[v]} U children's Out labels
        for (std::size_t i = topo.size(); i-- > 0;) {
            vid_t v = topo[i];
            std::vector<vid_t> cands; cands.push_back(pi[v]);
            for (const vid_t* it = dag.out_begin(v); it != dag.out_end(v); ++it) {
                const std::vector<vid_t>& c = lout_[(std::size_t)p * n_ + *it];
                cands.insert(cands.end(), c.begin(), c.end());
            }
            keep_topk(lout_[(std::size_t)p * n_ + v], cands, k_);
        }
        // In labels: topo order, mink over {pi[v]} U predecessors' In labels
        for (vid_t v : topo) {
            std::vector<vid_t> cands; cands.push_back(pi[v]);
            for (const vid_t* it = rev.out_begin(v); it != rev.out_end(v); ++it) {
                const std::vector<vid_t>& c = lin_[(std::size_t)p * n_ + *it];
                cands.insert(cands.end(), c.begin(), c.end());
            }
            keep_topk(lin_[(std::size_t)p * n_ + v], cands, k_);
        }
    }
}

namespace {
// Theorem 4.1: returns true if B is provably NOT a subset of A, given MA = mink(pi(A)),
// MB = mink(pi(B)) (sorted ascending, size <= k). True => some pi-value of B is certainly absent
// from A.
inline bool not_subset(const std::vector<vid_t>& MA, const std::vector<vid_t>& MB, int k) {
    const bool a_full = (int)MA.size() == k;
    const vid_t a_max = MA.empty() ? 0 : MA.back();
    for (vid_t x : MB) {
        if (a_full && x >= a_max) break;                       // remaining are larger: inconclusive
        if (!std::binary_search(MA.begin(), MA.end(), x)) {    // x not among A's k smallest
            if (!a_full || x < a_max) return true;             // => x certainly not in A
        }
    }
    return false;
}
}  // namespace

int IP::neg_cut(vid_t u, vid_t v) const {
    if (level_[u] >= level_[v]) return 1;                       // Level label: Lup(u) >= Lup(v)
    if (ldown_[u] <= ldown_[v]) return 1;                       // Level label: Ldown(u) <= Ldown(v)
    for (int p = 0; p < np_; ++p) {
        const std::size_t o = (std::size_t)p * n_;
        if (not_subset(lout_[o + u], lout_[o + v], k_)) return 1;   // Out(v) !subset Out(u)
        if (not_subset(lin_[o + v], lin_[o + u], k_)) return 1;     // In(u) !subset In(v)
    }
    return 0;
}

int IP::hv_cut(vid_t c, vid_t v) const {
    if (h_ <= 0 || outdeg_[c] <= (vid_t)mu_) return 0;          // c is not a huge vertex
    const std::vector<vid_t>& L = lhv_[v];
    if (std::binary_search(L.begin(), L.end(), c)) return 1;    // c reaches v (c in Lhv(v))
    if ((int)L.size() < h_) return -1;                         // room left, yet c absent -> c !-> v
    vid_t mind = outdeg_[L[0]];                                 // Lhv(v) is full: compare out-degrees
    for (vid_t w : L) mind = std::min(mind, outdeg_[w]);
    if (outdeg_[c] > mind) return -1;                          // c would outrank a member -> c !-> v
    return 0;
}

bool IP::reaches(vid_t u, vid_t v) {
    if (u == v) return true;
    if (neg_cut(u, v)) return false;
    { int hv = hv_cut(u, v); if (hv > 0) return true; if (hv < 0) return false; }

    ++query_cnt_;
    const int qc = query_cnt_;
    std::vector<vid_t> st;
    st.push_back(u); stamp_[u] = qc;
    while (!st.empty()) {
        vid_t x = st.back(); st.pop_back();
        for (const vid_t* it = fwd_.out_begin(x); it != fwd_.out_end(x); ++it) {
            vid_t c = *it;
            if (c == v) return true;
            if (stamp_[c] == qc) continue;
            if (neg_cut(c, v)) continue;          // c certainly cannot reach v -> prune
            int hv = hv_cut(c, v);
            if (hv > 0) return true;              // c reaches v via the HV-Label
            if (hv < 0) continue;                 // c certainly cannot reach v -> prune
            stamp_[c] = qc; st.push_back(c);
        }
    }
    return false;
}

std::size_t IP::index_size_bytes() const {
    std::size_t b = (level_.size() + ldown_.size() + outdeg_.size()) * sizeof(vid_t);
    for (const auto& l : lout_) b += l.size() * sizeof(vid_t);
    for (const auto& l : lin_) b += l.size() * sizeof(vid_t);
    for (const auto& l : lhv_) b += l.size() * sizeof(vid_t);
    return b;
}

}  // namespace reachability
