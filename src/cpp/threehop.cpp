#include "reachability/threehop.hpp"
#include <algorithm>
#include <cstdint>
#include <unordered_map>
#include <vector>

namespace reachability {

namespace {
// Linear 2-approximation for the densest subgraph: drop the minimum-degree vertex repeatedly,
// keep the densest snapshot. Returns the kept node indices.
std::vector<vid_t> densest_subgraph(const std::vector<std::vector<vid_t>>& adj) {
    const vid_t nv = static_cast<vid_t>(adj.size());
    std::vector<vid_t> deg(nv);
    long long edges = 0;
    for (vid_t i = 0; i < nv; ++i) { deg[i] = (vid_t)adj[i].size(); edges += deg[i]; }
    edges /= 2;
    std::vector<char> removed(nv, 0);
    std::vector<vid_t> seq; seq.reserve(nv);
    long long curEdges = edges; vid_t curNodes = nv;
    double best = curNodes > 0 ? (double)curEdges / curNodes : 0.0;
    vid_t bestRemoved = 0;
    while (curNodes > 0) {
        vid_t x = -1, md = 0;
        for (vid_t i = 0; i < nv; ++i)
            if (!removed[i] && (x < 0 || deg[i] < md)) { x = i; md = deg[i]; }
        removed[x] = 1; seq.push_back(x); curEdges -= deg[x];
        for (vid_t y : adj[x]) if (!removed[y]) --deg[y];
        --curNodes;
        if (curNodes > 0) { double d = (double)curEdges / curNodes; if (d > best) { best = d; bestRemoved = (vid_t)seq.size(); } }
    }
    std::vector<vid_t> kept;
    for (std::size_t i = bestRemoved; i < seq.size(); ++i) kept.push_back(seq[i]);
    return kept;
}
}  // namespace

void ThreeHop::build(const CSRGraph& dag) {
    n_ = dag.num_nodes();
    cid_.assign(n_, -1); pos_.assign(n_, 0);
    entry_recs_.clear(); exit_recs_.clear();
    if (n_ == 0) return;

    // ---- chain decomposition (greedy edge-path cover, as in ChainCover) ----
    std::vector<vid_t> indeg(n_, 0);
    for (vid_t u = 0; u < n_; ++u)
        for (const vid_t* it = dag.out_begin(u); it != dag.out_end(u); ++it) ++indeg[*it];
    std::vector<vid_t> topo; topo.reserve(n_);
    {
        std::vector<vid_t> ind = indeg, q;
        for (vid_t u = 0; u < n_; ++u) if (ind[u] == 0) q.push_back(u);
        std::size_t h = 0;
        while (h < q.size()) { vid_t u = q[h++]; topo.push_back(u);
            for (const vid_t* it = dag.out_begin(u); it != dag.out_end(u); ++it)
                if (--ind[*it] == 0) q.push_back(*it); }
    }
    std::vector<char> covered(n_, 0);
    std::vector<std::vector<vid_t>> chains;
    for (vid_t s : topo) {
        if (covered[s]) continue;
        vid_t cur = s; std::vector<vid_t> ch;
        for (;;) {
            covered[cur] = 1; cid_[cur] = (vid_t)chains.size(); pos_[cur] = (vid_t)ch.size();
            ch.push_back(cur);
            vid_t next = -1;
            for (const vid_t* it = dag.out_begin(cur); it != dag.out_end(cur); ++it)
                if (!covered[*it]) { next = *it; break; }
            if (next < 0) break;
            cur = next;
        }
        chains.push_back(std::move(ch));
    }
    const vid_t K = (vid_t)chains.size();
    entry_recs_.resize(K); exit_recs_.resize(K);

    // ---- transitive closure as bitsets: reach_[u] = {u} U descendants ----
    const vid_t W = (n_ + 63) / 64;
    std::vector<std::uint64_t> reach((std::size_t)n_ * W, 0);
    auto rset = [&](vid_t u, vid_t b){ reach[(std::size_t)u * W + (b >> 6)] |= (std::uint64_t)1 << (b & 63); };
    auto rget = [&](vid_t u, vid_t b)->bool { return (reach[(std::size_t)u * W + (b >> 6)] >> (b & 63)) & 1ULL; };
    for (std::size_t i = topo.size(); i-- > 0;) {
        vid_t u = topo[i]; rset(u, u);
        for (const vid_t* it = dag.out_begin(u); it != dag.out_end(u); ++it) {
            std::uint64_t* du = &reach[(std::size_t)u * W];
            const std::uint64_t* dv = &reach[(std::size_t)(*it) * W];
            for (vid_t k = 0; k < W; ++k) du[k] |= dv[k];
        }
    }

    // ---- ent[v][m] = min pos on chain m reachable from v; ext[v][m] = max pos on m reaching v (-1 = none)
    std::vector<vid_t> ent((std::size_t)n_ * K, -1), ext((std::size_t)n_ * K, -1);
    for (vid_t v = 0; v < n_; ++v) {
        for (vid_t m = 0; m < K; ++m) {
            const std::vector<vid_t>& ch = chains[m];
            vid_t e = -1;
            for (vid_t pp = 0; pp < (vid_t)ch.size(); ++pp) if (rget(v, ch[pp])) { e = pp; break; }
            ent[(std::size_t)v * K + m] = e;
            vid_t x = -1;
            for (vid_t pp = (vid_t)ch.size(); pp-- > 0;) if (rget(ch[pp], v)) { x = pp; break; }
            ext[(std::size_t)v * K + m] = x;
        }
    }
    auto ENT = [&](vid_t v, vid_t m)->vid_t { return ent[(std::size_t)v * K + m]; };
    auto EXT = [&](vid_t v, vid_t m)->vid_t { return ext[(std::size_t)v * K + m]; };

    // ---- transitive closure contour: pseudo-diagonal cells per ordered chain pair (Ci, Cj) ----
    std::vector<std::pair<vid_t, vid_t>> con;   // (out-anchor, in-anchor)
    for (vid_t ci = 0; ci < K; ++ci) {
        const std::vector<vid_t>& Ci = chains[ci];
        for (vid_t cj = 0; cj < K; ++cj) {
            if (cj == ci) continue;
            for (vid_t a = 0; a < (vid_t)Ci.size(); ++a) {
                vid_t va = Ci[a];
                vid_t fa = ENT(va, cj);              // pos of f(va) on Cj (-1 = +inf)
                if (fa < 0) continue;                // f(va)=inf cannot be a pseudo-diagonal cell
                bool keep;
                if (a + 1 == (vid_t)Ci.size()) keep = true;          // last vertex: 1-cell -> contour
                else { vid_t fn = ENT(Ci[a + 1], cj); keep = (fn < 0) || (fn > fa); }  // f strictly increases
                if (keep) con.emplace_back(va, chains[cj][fa]);
            }
        }
    }

    // ---- greedy factorization (set cover via densest subgraph of chain-center bipartite graphs)
    std::vector<char> uncov(con.size(), 1);
    long long remaining = (long long)con.size();
    while (remaining > 0) {
        double bestDensity = -1.0; vid_t bestChain = -1;
        std::vector<vid_t> bestX, bestY;
        for (vid_t m = 0; m < K; ++m) {
            // bipartite graph over uncovered contour pairs routable through chain m
            std::unordered_map<vid_t, vid_t> lidx, ridx;   // vertex -> local node id
            std::vector<vid_t> lvert, rvert;
            std::vector<std::pair<vid_t, vid_t>> edges;     // (left local, right local)
            for (std::size_t pi = 0; pi < con.size(); ++pi) {
                if (!uncov[pi]) continue;
                vid_t x = con[pi].first, y = con[pi].second;
                vid_t ex = ENT(x, m), xy = EXT(y, m);
                if (ex < 0 || xy < 0 || ex > xy) continue;  // not routable via chain m
                auto li = lidx.find(x); vid_t l;
                if (li == lidx.end()) { l = (vid_t)lvert.size(); lidx[x] = l; lvert.push_back(x); }
                else l = li->second;
                auto ri = ridx.find(y); vid_t r;
                if (ri == ridx.end()) { r = (vid_t)rvert.size(); ridx[y] = r; rvert.push_back(y); }
                else r = ri->second;
                edges.emplace_back(l, r);
            }
            if (edges.empty()) continue;
            vid_t a = (vid_t)lvert.size(), b = (vid_t)rvert.size();
            std::vector<std::vector<vid_t>> adj(a + b);
            for (auto& e : edges) { adj[e.first].push_back(a + e.second); adj[a + e.second].push_back(e.first); }
            std::vector<vid_t> kept = densest_subgraph(adj);
            double density = 0.0;
            {
                std::vector<char> in(a + b, 0); for (vid_t z : kept) in[z] = 1;
                long long ke = 0; for (auto& e : edges) if (in[e.first] && in[a + e.second]) ++ke;
                if (!kept.empty()) density = (double)ke / kept.size();
            }
            if (density > bestDensity) {
                bestDensity = density; bestChain = m;
                bestX.clear(); bestY.clear();
                for (vid_t z : kept) { if (z < a) bestX.push_back(lvert[z]); else bestY.push_back(rvert[z - a]); }
            }
        }
        if (bestChain < 0) break;   // safety (should not happen: every pair routable via in-anchor's chain)

        std::vector<char> inX(n_, 0), inY(n_, 0);
        for (vid_t x : bestX) { inX[x] = 1; entry_recs_[cid_[x]].push_back({pos_[x], bestChain, ENT(x, bestChain)}); }
        for (vid_t y : bestY) { inY[y] = 1; exit_recs_[cid_[y]].push_back({pos_[y], bestChain, EXT(y, bestChain)}); }
        for (std::size_t pi = 0; pi < con.size(); ++pi) {
            if (!uncov[pi]) continue;
            vid_t x = con[pi].first, y = con[pi].second;
            if (inX[x] && inY[y]) {
                vid_t ex = ENT(x, bestChain), xy = EXT(y, bestChain);
                if (ex >= 0 && xy >= 0 && ex <= xy) { uncov[pi] = 0; --remaining; }
            }
        }
    }

    for (vid_t c = 0; c < K; ++c) {
        auto by_pos = [](const Rec& p, const Rec& q){ return p.pos < q.pos; };
        std::sort(entry_recs_[c].begin(), entry_recs_[c].end(), by_pos);
        std::sort(exit_recs_[c].begin(), exit_recs_[c].end(), by_pos);
    }
}

bool ThreeHop::query(vid_t u, vid_t v) const {
    if (u == v) return true;
    if (cid_[u] == cid_[v]) return pos_[u] <= pos_[v];   // same chain

    // u's entry into each highway = min entry over anchors at pos >= pos_[u] on u's chain
    std::unordered_map<vid_t, vid_t> ue;
    for (const Rec& r : entry_recs_[cid_[u]]) {
        if (r.pos < pos_[u]) continue;
        auto it = ue.find(r.hw);
        if (it == ue.end() || r.val < it->second) ue[r.hw] = r.val;
    }
    if (ue.empty()) return false;
    // v's exit from each highway = max exit over anchors at pos <= pos_[v]; a match needs entry <= exit
    for (const Rec& r : exit_recs_[cid_[v]]) {
        if (r.pos > pos_[v]) continue;
        auto it = ue.find(r.hw);
        if (it != ue.end() && it->second <= r.val) return true;
    }
    return false;
}

std::size_t ThreeHop::index_size_bytes() const {
    std::size_t b = (cid_.size() + pos_.size()) * sizeof(vid_t);
    for (const auto& r : entry_recs_) b += r.size() * sizeof(Rec);
    for (const auto& r : exit_recs_) b += r.size() * sizeof(Rec);
    return b;
}

}  // namespace reachability
