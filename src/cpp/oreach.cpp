#include "reachability/oreach.hpp"
#include "reachability/levels.hpp"
#include <algorithm>
#include <functional>
#include <numeric>
#include <random>
#include <vector>

namespace reachability {

namespace {
// Extended topological sort (Tarjan back-to-front, iterative). Returns tau (topological index,
// source small), tauH (high index = largest contiguously reachable index) and tauX (max index =
// largest reachable index). Start vertices and out-neighbours are visited in a shuffled order.
void extended_topsort(const CSRGraph& g, unsigned seed,
                      std::vector<vid_t>& tau, std::vector<vid_t>& tauH, std::vector<vid_t>& tauX) {
    const vid_t n = g.num_nodes();
    tau.assign(n, 0); tauH.assign(n, 0); tauX.assign(n, 0);
    std::vector<char> visited(n, 0);
    std::mt19937 rng(seed);

    // Start from sources (in random order), then any remaining vertices, so the first non-recursive
    // Visit is always a source — this maximises the [tau, tauH] ranges (paper Sect. 4.1).
    std::vector<vid_t> indeg(n, 0);
    for (vid_t u = 0; u < n; ++u)
        for (const vid_t* it = g.out_begin(u); it != g.out_end(u); ++it) ++indeg[*it];
    std::vector<vid_t> sources, rest;
    for (vid_t v = 0; v < n; ++v) (indeg[v] == 0 ? sources : rest).push_back(v);
    std::shuffle(sources.begin(), sources.end(), rng);
    std::shuffle(rest.begin(), rest.end(), rng);
    std::vector<vid_t> starts;
    starts.reserve(n);
    starts.insert(starts.end(), sources.begin(), sources.end());
    starts.insert(starts.end(), rest.begin(), rest.end());

    // shuffled out-neighbour lists
    std::vector<std::vector<vid_t>> adj(n);
    for (vid_t u = 0; u < n; ++u) {
        adj[u].assign(g.out_begin(u), g.out_end(u));
        std::shuffle(adj[u].begin(), adj[u].end(), rng);
    }

    vid_t i = n == 0 ? 0 : n - 1;
    struct F { vid_t v; std::size_t ci; };
    std::vector<F> st;
    for (vid_t s : starts) {
        if (visited[s]) continue;
        visited[s] = 1; tauH[s] = i;
        st.push_back({s, 0});
        while (!st.empty()) {
            F& f = st.back();
            if (f.ci < adj[f.v].size()) {
                vid_t u = adj[f.v][f.ci++];
                if (!visited[u]) { visited[u] = 1; tauH[u] = i; st.push_back({u, 0}); }
            } else {
                vid_t v = f.v;
                vid_t m = tauH[v];
                for (vid_t u : adj[v]) m = std::max(m, tauX[u]);
                tauX[v] = m;
                tau[v] = i; if (i > 0) --i;
                st.pop_back();
            }
        }
    }
}

CSRGraph reverse_of(const CSRGraph& g) {
    const vid_t n = g.num_nodes();
    std::vector<vid_t> rs, rd;
    rs.reserve(g.num_edges()); rd.reserve(g.num_edges());
    for (vid_t u = 0; u < n; ++u)
        for (const vid_t* it = g.out_begin(u); it != g.out_end(u); ++it) { rs.push_back(*it); rd.push_back(u); }
    return CSRGraph(n, rs, rd);
}

// BFS count of vertices reachable from src in g (excluding src).
vid_t bfs_count(const CSRGraph& g, vid_t src, std::vector<char>& seen, std::vector<vid_t>& q) {
    vid_t cnt = 0, qs = 0, qt = 0;
    seen[src] = 1; q[qt++] = src;
    while (qs != qt) {
        vid_t v = q[qs++];
        for (const vid_t* it = g.out_begin(v); it != g.out_end(v); ++it)
            if (!seen[*it]) { seen[*it] = 1; q[qt++] = *it; ++cnt; }
    }
    for (vid_t j = 0; j < qt; ++j) seen[q[j]] = 0;
    return cnt;
}
}  // namespace

void OReach::build(const CSRGraph& dag, int k, int p, int h, int t, unsigned seed) {
    n_ = dag.num_nodes();
    fwd_ = dag;
    F_ = topological_levels(dag);
    rev_ = reverse_of(dag);
    B_ = topological_levels(rev_);
    stamp_.assign(n_, 0); bstamp_.assign(n_, 0);
    query_cnt_ = 0;
    ords_.clear();
    rin_.assign(n_, 0); rout_.assign(n_, 0); nsupp_ = 0;
    wcc_.assign(n_, 0);
    if (n_ == 0) return;

    // ---- weakly-connected components (Observation B2): union-find over undirected edges ----
    {
        std::vector<vid_t> uf(n_);
        std::iota(uf.begin(), uf.end(), 0);
        std::function<vid_t(vid_t)> find = [&](vid_t x){ while (uf[x] != x) { uf[x] = uf[uf[x]]; x = uf[x]; } return x; };
        for (vid_t u = 0; u < n_; ++u)
            for (const vid_t* it = dag.out_begin(u); it != dag.out_end(u); ++it) {
                vid_t a = find(u), b = find(*it); if (a != b) uf[a] = b;
            }
        for (vid_t v = 0; v < n_; ++v) wcc_[v] = find(v);
    }

    // ---- supportive vertices (paper's slim-level selection) ----
    int kk = std::min({k, (int)n_, 64});
    if (kk > 0) {
        if (h < 1) h = 1;
        vid_t Lmax = 0;
        for (vid_t v = 0; v < n_; ++v) Lmax = std::max(Lmax, F_[v]);
        // per-level vertex counts (forward and backward) to identify slim levels
        std::vector<vid_t> fcnt(Lmax + 1, 0), bcnt(n_, 0);
        vid_t Bmax = 0;
        for (vid_t v = 0; v < n_; ++v) { ++fcnt[F_[v]]; Bmax = std::max(Bmax, B_[v]); }
        bcnt.assign(Bmax + 1, 0);
        for (vid_t v = 0; v < n_; ++v) ++bcnt[B_[v]];

        const long long cap = (long long)kk * std::max(1, p);
        std::vector<char> inCand(n_, 0);
        std::vector<vid_t> cand;
        std::mt19937 rng(seed + 991);
        for (vid_t v = 0; v < n_ && (long long)cand.size() < cap; ++v)   // all slim-level vertices
            if (fcnt[F_[v]] <= (vid_t)h || bcnt[B_[v]] <= (vid_t)h) { inCand[v] = 1; cand.push_back(v); }
        if ((long long)cand.size() < cap) {                              // fill from central fwd levels
            vid_t lo = Lmax / 5, hi = (vid_t)((4.0 * Lmax) / 5.0);
            std::vector<vid_t> pool;
            for (vid_t v = 0; v < n_; ++v) if (!inCand[v] && F_[v] >= lo && F_[v] <= hi) pool.push_back(v);
            std::shuffle(pool.begin(), pool.end(), rng);
            for (vid_t v : pool) { if ((long long)cand.size() >= cap) break; inCand[v] = 1; cand.push_back(v); }
        }
        for (vid_t v = 0; v < n_ && (int)cand.size() < kk; ++v)          // ensure >= kk on tiny graphs
            if (!inCand[v]) { inCand[v] = 1; cand.push_back(v); }

        // score candidates by |R+(v)| * |R-(v)|, pick the k largest
        std::vector<char> seen(n_, 0);
        std::vector<vid_t> q(n_);
        std::vector<std::pair<long long, vid_t>> scored;
        scored.reserve(cand.size());
        for (vid_t v : cand) {
            long long ro = bfs_count(fwd_, v, seen, q);
            long long ri = bfs_count(rev_, v, seen, q);
            scored.push_back({ro * ri, v});
        }
        std::sort(scored.begin(), scored.end(), std::greater<std::pair<long long, vid_t>>());

        nsupp_ = std::min(kk, (int)scored.size());
        for (int j = 0; j < nsupp_; ++j) {
            vid_t v = scored[j].second;
            std::uint64_t bit = (std::uint64_t)1 << j;
            // R+(v): forward BFS -> rout bit
            vid_t qs = 0, qt = 0; seen[v] = 1; q[qt++] = v; rout_[v] |= bit;
            while (qs != qt) { vid_t x = q[qs++];
                for (const vid_t* it = fwd_.out_begin(x); it != fwd_.out_end(x); ++it)
                    if (!seen[*it]) { seen[*it] = 1; q[qt++] = *it; rout_[*it] |= bit; } }
            for (vid_t z = 0; z < qt; ++z) seen[q[z]] = 0;
            // R-(v): backward BFS -> rin bit
            qs = qt = 0; seen[v] = 1; q[qt++] = v; rin_[v] |= bit;
            while (qs != qt) { vid_t x = q[qs++];
                for (const vid_t* it = rev_.out_begin(x); it != rev_.out_end(x); ++it)
                    if (!seen[*it]) { seen[*it] = 1; q[qt++] = *it; rin_[*it] |= bit; } }
            for (vid_t z = 0; z < qt; ++z) seen[q[z]] = 0;
        }
    }

    // ---- extended topological orderings (started from sources; half via the reverse graph) ----
    int tt = std::max(0, t);
    for (int j = 0; j < tt; ++j) {
        bool forward = (j % 2 == 0);
        Ordering o; o.forward = forward;
        std::vector<vid_t> tau, tH, tX;
        if (forward) {
            extended_topsort(fwd_, seed + 1357 * (unsigned)j, tau, tH, tX);
            o.tau = std::move(tau); o.a = std::move(tH); o.b = std::move(tX);   // a=high, b=max
        } else {
            extended_topsort(rev_, seed + 1357 * (unsigned)j, tau, tH, tX);
            // map reverse ordering back to the original graph
            o.tau.assign(n_, 0); o.a.assign(n_, 0); o.b.assign(n_, 0);
            for (vid_t v = 0; v < n_; ++v) {
                o.tau[v] = (n_ - 1) - tau[v];
                o.a[v]   = (n_ - 1) - tH[v];   // low index
                o.b[v]   = (n_ - 1) - tX[v];   // min index
            }
        }
        ords_.push_back(std::move(o));
    }
}

int OReach::apply_ord(const Ordering& o, vid_t s, vid_t t) const {
    if (o.forward) {
        if (o.tau[t] < o.tau[s]) return -1;                                  // B4
        if (o.tau[s] <= o.tau[t] && o.tau[t] <= o.a[s]) return 1;            // T1
        if (o.tau[t] > o.b[s]) return -1;                                    // T2
        if (o.tau[t] == o.b[s]) return 1;                                    // T3
    } else {
        if (o.tau[t] < o.tau[s]) return -1;                                  // B4
        if (o.a[t] <= o.tau[s] && o.tau[s] <= o.tau[t]) return 1;            // T4
        if (o.tau[s] < o.b[t]) return -1;                                    // T5
        if (o.tau[s] == o.b[t]) return 1;                                    // T6
    }
    return 0;
}

int OReach::observe(vid_t s, vid_t t) const {
    // Paper's test order (alternating positive/negative; all constant time).
    if (F_[s] >= F_[t]) return -1;                       // Test 2: B5 (covers B1)
    if (B_[s] <= B_[t]) return -1;                       // Test 2: B6
    if (nsupp_ > 0 && (rin_[s] & rout_[t])) return 1;    // Test 3: S1 (positive)
    if (!ords_.empty()) { int r = apply_ord(ords_[0], s, t); if (r) return r; }   // Test 4
    if (nsupp_ > 0) {                                    // Test 5: S2, S3 (negative)
        if (rout_[s] & ~rout_[t]) return -1;
        if (~rin_[s] & rin_[t]) return -1;
    }
    for (std::size_t j = 1; j < ords_.size(); ++j) { int r = apply_ord(ords_[j], s, t); if (r) return r; }  // Test 6
    if (wcc_[s] != wcc_[t]) return -1;                   // Test 7: B2 (different WCC)
    return 0;
}

bool OReach::reaches(vid_t s, vid_t t) {
    if (s == t) return true;
    int o = observe(s, t);
    if (o > 0) return true;
    if (o < 0) return false;

    // Pruning bidirectional BFS: on each newly seen vertex v, test Query(v,t) (forward) or
    // Query(s,v) (backward) with the observations — positive => answer yes, negative => prune v.
    ++query_cnt_;
    const int qc = query_cnt_;
    std::vector<vid_t> fq, bq, nfq, nbq;
    fq.push_back(s); stamp_[s] = qc;
    bq.push_back(t); bstamp_[t] = qc;
    while (!fq.empty() && !bq.empty()) {
        if (fq.size() <= bq.size()) {                    // expand the smaller forward frontier
            nfq.clear();
            for (vid_t x : fq)
                for (const vid_t* it = fwd_.out_begin(x); it != fwd_.out_end(x); ++it) {
                    vid_t c = *it;
                    if (bstamp_[c] == qc || c == t) return true;       // met the backward search
                    if (stamp_[c] == qc) continue;
                    int oc = observe(c, t);
                    if (oc > 0) return true;
                    if (oc < 0) continue;                               // prune: c cannot reach t
                    stamp_[c] = qc; nfq.push_back(c);
                }
            fq.swap(nfq);
        } else {                                         // expand the smaller backward frontier
            nbq.clear();
            for (vid_t x : bq)
                for (const vid_t* it = rev_.out_begin(x); it != rev_.out_end(x); ++it) {
                    vid_t c = *it;
                    if (stamp_[c] == qc || c == s) return true;        // met the forward search
                    if (bstamp_[c] == qc) continue;
                    int oc = observe(s, c);
                    if (oc > 0) return true;
                    if (oc < 0) continue;                               // prune: s cannot reach c
                    bstamp_[c] = qc; nbq.push_back(c);
                }
            bq.swap(nbq);
        }
    }
    return false;
}

std::size_t OReach::index_size_bytes() const {
    std::size_t b = (F_.size() + B_.size() + wcc_.size()) * sizeof(vid_t);
    b += (rin_.size() + rout_.size()) * sizeof(std::uint64_t);
    for (const Ordering& o : ords_) b += (o.tau.size() + o.a.size() + o.b.size()) * sizeof(vid_t);
    return b;
}

}  // namespace reachability
