#include "reachability/optimal_tree.hpp"
#include <cstdint>
#include <vector>

namespace reachability {

std::vector<vid_t> optimal_tree_parent(const CSRGraph& dag) {
    const vid_t n = dag.num_nodes();
    std::vector<vid_t> parent(n, -1);
    if (n == 0) return parent;

    // reverse graph (in-neighbours) + topological order (Kahn)
    std::vector<vid_t> indeg(n, 0), rs, rd;
    rs.reserve(dag.num_edges()); rd.reserve(dag.num_edges());
    for (vid_t u = 0; u < n; ++u)
        for (const vid_t* it = dag.out_begin(u); it != dag.out_end(u); ++it) { ++indeg[*it]; rs.push_back(*it); rd.push_back(u); }
    CSRGraph rev(n, rs, rd);
    std::vector<vid_t> topo; topo.reserve(n);
    {
        std::vector<vid_t> ind = indeg, q;
        for (vid_t u = 0; u < n; ++u) if (ind[u] == 0) q.push_back(u);
        std::size_t h = 0;
        while (h < q.size()) { vid_t u = q[h++]; topo.push_back(u);
            for (const vid_t* it = dag.out_begin(u); it != dag.out_end(u); ++it)
                if (--ind[*it] == 0) q.push_back(*it); }
    }

    // pred[j] = {j} U union over in-neighbours i of pred[i]  (reverse reachability), in topo order
    const vid_t W = (n + 63) / 64;
    std::vector<std::uint64_t> pred((std::size_t)n * W, 0);
    std::vector<vid_t> psize(n, 0);
    for (vid_t v : topo) {
        std::uint64_t* pv = &pred[(std::size_t)v * W];
        pv[v >> 6] |= (std::uint64_t)1 << (v & 63);
        for (const vid_t* it = rev.out_begin(v); it != rev.out_end(v); ++it) {
            const std::uint64_t* pi = &pred[(std::size_t)(*it) * W];
            for (vid_t k = 0; k < W; ++k) pv[k] |= pi[k];
        }
        vid_t c = 0;
        for (vid_t k = 0; k < W; ++k) { std::uint64_t x = pv[k]; for (; x; x &= x - 1) ++c; }
        psize[v] = c;
    }

    // tree parent of j = the in-neighbour i maximising |pred(i)| (ties: smaller id)
    for (vid_t j = 0; j < n; ++j) {
        vid_t best = -1, bestsz = 0;
        for (const vid_t* it = rev.out_begin(j); it != rev.out_end(j); ++it) {
            vid_t i = *it;
            if (best < 0 || psize[i] > bestsz || (psize[i] == bestsz && i < best)) { best = i; bestsz = psize[i]; }
        }
        parent[j] = best;   // -1 if j is a source
    }
    return parent;
}

}  // namespace reachability
