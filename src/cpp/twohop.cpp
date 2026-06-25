#include "reachability/twohop.hpp"
#include "reachability/levels.hpp"
#include <algorithm>
#include <cstdint>
#include <vector>

namespace reachability {

namespace {
// Portable popcount (MSVC lacks __builtin_popcountll); only used in construction, not on the
// query path, so Kernighan's bit-clearing loop is fine.
inline int popcount64(uint64_t x) { int c = 0; for (; x; x &= x - 1) ++c; return c; }

// Linear-time 2-approximation for the densest subgraph (Cohen et al., from Kortsarz & Peleg):
// repeatedly remove the minimum-degree vertex and return the densest snapshot seen. `adj` is an
// undirected graph on `nv` vertices; returns the kept vertices and their induced density.
struct DensestResult { std::vector<vid_t> kept; double density; };

DensestResult densest_subgraph(const std::vector<std::vector<vid_t>>& adj) {
    const vid_t nv = static_cast<vid_t>(adj.size());
    std::vector<vid_t> deg(nv);
    long long edges = 0;
    for (vid_t i = 0; i < nv; ++i) { deg[i] = static_cast<vid_t>(adj[i].size()); edges += deg[i]; }
    edges /= 2;

    std::vector<char> removed(nv, 0);
    std::vector<vid_t> seq;             // removal order
    seq.reserve(nv);

    long long curEdges = edges;
    vid_t curNodes = nv;
    double best = (curNodes > 0) ? static_cast<double>(curEdges) / curNodes : 0.0;
    vid_t bestRemoved = 0;              // keep nodes removed at step >= bestRemoved

    while (curNodes > 0) {
        // minimum-degree present vertex
        vid_t x = -1;
        vid_t md = 0;
        for (vid_t i = 0; i < nv; ++i)
            if (!removed[i] && (x < 0 || deg[i] < md)) { x = i; md = deg[i]; }
        removed[x] = 1; seq.push_back(x);
        curEdges -= deg[x];
        for (vid_t y : adj[x]) if (!removed[y]) --deg[y];
        --curNodes;
        if (curNodes > 0) {
            double d = static_cast<double>(curEdges) / curNodes;
            if (d > best) { best = d; bestRemoved = static_cast<vid_t>(seq.size()); }
        }
    }

    DensestResult r;
    r.density = best;
    for (std::size_t i = bestRemoved; i < seq.size(); ++i) r.kept.push_back(seq[i]);
    return r;
}
}  // namespace

void TwoHop::build(const CSRGraph& dag) {
    n_ = dag.num_nodes();
    L_.resize(n_);
    level_ = topological_levels(dag);
    if (n_ == 0) return;

    const vid_t W = (n_ + 63) / 64;   // 64-bit words per bitset row

    // reverse graph (predecessors)
    std::vector<vid_t> rs, rd;
    rs.reserve(dag.num_edges()); rd.reserve(dag.num_edges());
    for (vid_t u = 0; u < n_; ++u)
        for (const vid_t* it = dag.out_begin(u); it != dag.out_end(u); ++it) {
            rs.push_back(*it); rd.push_back(u);
        }
    CSRGraph rdag(n_, rs, rd);

    // topological order (Kahn)
    std::vector<vid_t> topo; topo.reserve(n_);
    {
        std::vector<vid_t> indeg(n_, 0);
        for (vid_t u = 0; u < n_; ++u)
            for (const vid_t* it = dag.out_begin(u); it != dag.out_end(u); ++it)
                ++indeg[*it];
        std::vector<vid_t> q;
        for (vid_t u = 0; u < n_; ++u) if (indeg[u] == 0) q.push_back(u);
        std::size_t h = 0;
        while (h < q.size()) {
            vid_t u = q[h++]; topo.push_back(u);
            for (const vid_t* it = dag.out_begin(u); it != dag.out_end(u); ++it)
                if (--indeg[*it] == 0) q.push_back(*it);
        }
    }

    // Reachability closures as bitsets:
    //   desc[w] = vertices reachable from w (incl. w)   (reverse topo: {w} | union of succ)
    //   anc[w]  = vertices that reach w (incl. w)        (topo order: {w} | union of pred)
    std::vector<uint64_t> desc(static_cast<std::size_t>(n_) * W, 0);
    std::vector<uint64_t> anc (static_cast<std::size_t>(n_) * W, 0);
    auto setbit = [&](std::vector<uint64_t>& B, vid_t row, vid_t b) {
        B[static_cast<std::size_t>(row) * W + (b >> 6)] |= static_cast<uint64_t>(1) << (b & 63);
    };
    auto orrow = [&](std::vector<uint64_t>& B, vid_t dstrow, vid_t srcrow) {
        uint64_t* d = &B[static_cast<std::size_t>(dstrow) * W];
        const uint64_t* s = &B[static_cast<std::size_t>(srcrow) * W];
        for (vid_t k = 0; k < W; ++k) d[k] |= s[k];
    };
    auto getbit = [&](const std::vector<uint64_t>& B, vid_t row, vid_t b) -> bool {
        return (B[static_cast<std::size_t>(row) * W + (b >> 6)] >> (b & 63)) & 1ULL;
    };
    for (std::size_t i = topo.size(); i-- > 0;) {
        vid_t w = topo[i];
        setbit(desc, w, w);
        for (const vid_t* it = dag.out_begin(w); it != dag.out_end(w); ++it) orrow(desc, w, *it);
    }
    for (std::size_t i = 0; i < topo.size(); ++i) {
        vid_t w = topo[i];
        setbit(anc, w, w);
        for (const vid_t* it = rdag.out_begin(w); it != rdag.out_end(w); ++it) orrow(anc, w, *it);
    }

    // Uncovered reachable pairs: uncov[u] = {v : u reaches v, u != v, not yet covered}.
    std::vector<uint64_t> uncov(static_cast<std::size_t>(n_) * W, 0);
    long long remaining = 0;
    for (vid_t u = 0; u < n_; ++u) {
        uint64_t* row = &uncov[static_cast<std::size_t>(u) * W];
        const uint64_t* d = &desc[static_cast<std::size_t>(u) * W];
        for (vid_t k = 0; k < W; ++k) row[k] = d[k];
        row[u >> 6] &= ~(static_cast<uint64_t>(1) << (u & 63));   // drop reflexive pair
        for (vid_t k = 0; k < W; ++k) remaining += popcount64(row[k]);
    }

    // Greedy set cover: each step adds the best center.
    std::vector<vid_t> Cin, Cout;
    while (remaining > 0) {
        double bestRatio = -1.0;
        vid_t bestW = -1;
        std::vector<vid_t> bestCin, bestCout;

        for (vid_t w = 0; w < n_; ++w) {
            Cin.clear(); Cout.clear();
            for (vid_t v = 0; v < n_; ++v) if (getbit(anc, w, v))  Cin.push_back(v);   // v -> w
            for (vid_t v = 0; v < n_; ++v) if (getbit(desc, w, v)) Cout.push_back(v);  // w -> v
            const vid_t a = static_cast<vid_t>(Cin.size());
            const vid_t b = static_cast<vid_t>(Cout.size());
            if (a == 0 || b == 0) continue;

            // bipartite center graph: nodes 0..a-1 = Cin, a..a+b-1 = Cout; edge iff pair uncovered
            std::vector<std::vector<vid_t>> adj(a + b);
            bool anyEdge = false;
            for (vid_t i = 0; i < a; ++i) {
                const uint64_t* row = &uncov[static_cast<std::size_t>(Cin[i]) * W];
                for (vid_t j = 0; j < b; ++j) {
                    vid_t v = Cout[j];
                    if ((row[v >> 6] >> (v & 63)) & 1ULL) {
                        adj[i].push_back(a + j);
                        adj[a + j].push_back(i);
                        anyEdge = true;
                    }
                }
            }
            if (!anyEdge) continue;

            DensestResult dr = densest_subgraph(adj);
            if (dr.density > bestRatio) {
                bestRatio = dr.density;
                bestW = w;
                bestCin.clear(); bestCout.clear();
                for (vid_t node : dr.kept) {
                    if (node < a) bestCin.push_back(Cin[node]);
                    else          bestCout.push_back(Cout[node - a]);
                }
            }
        }

        // Apply the chosen center (guaranteed non-empty while pairs remain).
        for (vid_t u : bestCin) L_.Lout[u].push_back(bestW);
        for (vid_t v : bestCout) L_.Lin[v].push_back(bestW);
        for (vid_t u : bestCin) {
            uint64_t* row = &uncov[static_cast<std::size_t>(u) * W];
            for (vid_t v : bestCout) {
                uint64_t mask = static_cast<uint64_t>(1) << (v & 63);
                if (row[v >> 6] & mask) { row[v >> 6] &= ~mask; --remaining; }
            }
        }
    }

    for (vid_t v = 0; v < n_; ++v) {
        std::sort(L_.Lout[v].begin(), L_.Lout[v].end());
        std::sort(L_.Lin[v].begin(), L_.Lin[v].end());
    }
}

bool TwoHop::query(vid_t u, vid_t v) const {
    if (u == v) return true;
    if (level_[u] >= level_[v]) return false;   // topological quick reject
    return two_hop_intersects(L_, u, v);
}

std::size_t TwoHop::index_size_bytes() const {
    return L_.size_bytes() + level_.size() * sizeof(vid_t);
}

}  // namespace reachability
