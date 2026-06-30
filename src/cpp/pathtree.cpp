#include "reachability/pathtree.hpp"
#include <algorithm>
#include <limits>
#include <vector>

namespace reachability {

namespace {

struct PEdge { vid_t u, v; long long w; };

// Chu-Liu/Edmonds *maximum* arborescence rooted at `root`. Returns, for each node v != root, the
// index into `edges` of its chosen incoming edge (res[root] = -1). Every non-root node must have at
// least one incoming edge (guaranteed here by the weight-0 virtual-root edges). O(V*E) per phase,
// with at most V phases — fine since the path-graph is small (K = path-decomposition width).
std::vector<int> max_arborescence(vid_t V, vid_t root, const std::vector<PEdge>& edges) {
    std::vector<long long> inw(V, std::numeric_limits<long long>::min());
    std::vector<int> ine(V, -1);
    for (int i = 0; i < (int)edges.size(); ++i) {
        const PEdge& e = edges[i];
        if (e.v != root && e.w > inw[e.v]) { inw[e.v] = e.w; ine[e.v] = i; }
    }
    // detect cycles in the "pick best in-edge" functional graph
    std::vector<int> id(V, -1), vis(V, -1);
    int cyc = 0;
    for (vid_t v = 0; v < V; ++v) {
        if (v == root) continue;
        vid_t u = v;
        while (u != root && vis[u] != (int)v && id[u] == -1) { vis[u] = (int)v; u = edges[ine[u]].u; }
        if (u != root && id[u] == -1) {                 // new cycle through u
            vid_t w = u;
            do { id[w] = cyc; w = edges[ine[w]].u; } while (w != u);
            ++cyc;
        }
    }
    if (cyc == 0) {                                       // no cycle: best in-edges form the tree
        std::vector<int> res(V, -1);
        for (vid_t v = 0; v < V; ++v) if (v != root) res[v] = ine[v];
        return res;
    }
    for (vid_t v = 0; v < V; ++v) if (id[v] == -1) id[v] = cyc++;   // singletons
    std::vector<PEdge> ne; std::vector<int> orig;        // contracted graph (weights discounted)
    for (int i = 0; i < (int)edges.size(); ++i) {
        const PEdge& e = edges[i];
        int a = id[e.u], b = id[e.v];
        if (a != b) { ne.push_back({(vid_t)a, (vid_t)b, e.w - inw[e.v]}); orig.push_back(i); }
    }
    std::vector<int> sub = max_arborescence((vid_t)cyc, (vid_t)id[root], ne);
    std::vector<int> res(V, -1);
    std::vector<char> ext(V, 0);
    for (int c = 0; c < cyc; ++c) {                       // expand: external edge into each component
        if (c == id[root]) continue;
        int se = sub[c];
        if (se < 0) continue;
        int oi = orig[se];
        res[edges[oi].v] = oi; ext[edges[oi].v] = 1;      // the real node the external edge enters
    }
    for (vid_t v = 0; v < V; ++v) if (v != root && !ext[v]) res[v] = ine[v];   // rest keep cycle edges
    return res;
}

}  // namespace

void PathTree::build(const CSRGraph& dag) {
    n_ = dag.num_nodes();
    pid_.assign(n_, -1); x_.assign(n_, 0);
    rc_.assign(n_, {});
    if (n_ == 0) return;

    // topological order (Kahn) + per-vertex topo rank
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
    std::vector<vid_t> trank(n_, 0);
    for (vid_t i = 0; i < (vid_t)topo.size(); ++i) trank[topo[i]] = i;

    // Step 1: Simon's path decomposition. Greedily follow the smallest-topo-rank unused successor.
    std::vector<std::vector<vid_t>> paths;
    std::vector<vid_t> sid(n_, 0);
    {
        std::vector<char> used(n_, 0);
        for (vid_t s : topo) {
            if (used[s]) continue;
            std::vector<vid_t> path;
            vid_t cur = s;
            for (;;) {
                used[cur] = 1; pid_[cur] = (vid_t)paths.size(); sid[cur] = (vid_t)path.size();
                path.push_back(cur);
                vid_t best = -1;
                for (const vid_t* it = dag.out_begin(cur); it != dag.out_end(cur); ++it)
                    if (!used[*it] && (best < 0 || trank[*it] < trank[best])) best = *it;
                if (best < 0) break;
                cur = best;
            }
            paths.push_back(std::move(path));
        }
    }
    const vid_t K = (vid_t)paths.size();

    // Step 2/3: weighted path-graph + maximum-weight SP-tree (Chu-Liu/Edmonds). Each node is a path;
    // edge Pi->Pj has the MinPathIndex weight w_{Pi->Pj} = |Pi[->u]| where u is the last vertex in Pi
    // reaching Pj (= max sid among Pi-endpoints of edges into Pj, plus one). A virtual root (id K)
    // links to every path with weight 0, so the maximum arborescence is a spanning forest that
    // maximises covered weight = minimises the residual index size (paper Section 2.3).
    std::vector<PEdge> pedges;
    {
        std::vector<vid_t> mark(K, -1);
        std::vector<long long> wbest(K, 0);
        std::vector<vid_t> touched;
        for (vid_t i = 0; i < K; ++i) {
            touched.clear();
            for (vid_t u : paths[i])
                for (const vid_t* it = dag.out_begin(u); it != dag.out_end(u); ++it) {
                    vid_t j = pid_[*it];
                    if (j == i) continue;
                    long long cand = (long long)sid[u] + 1;          // |Pi[->u]|
                    if (mark[j] != i) { mark[j] = i; wbest[j] = cand; touched.push_back(j); }
                    else if (cand > wbest[j]) wbest[j] = cand;
                }
            for (vid_t j : touched) pedges.push_back({i, j, wbest[j]});
        }
        for (vid_t j = 0; j < K; ++j) pedges.push_back({K, j, 0});   // virtual-root edges
    }
    std::vector<vid_t> ppar(K, -1), plevel(K, 0);
    std::vector<std::vector<vid_t>> pchild(K + 1);     // children in SP-tree (incl. virtual root K)
    {
        std::vector<int> sel = max_arborescence(K + 1, K, pedges);
        for (vid_t j = 0; j < K; ++j) { int ei = sel[j]; ppar[j] = (ei < 0) ? K : pedges[ei].u; }
        for (vid_t j = 0; j < K; ++j) pchild[ppar[j]].push_back(j);
        std::vector<vid_t> q;
        for (vid_t c : pchild[K]) { plevel[c] = 1; q.push_back(c); }
        std::size_t head = 0;
        while (head < q.size()) { vid_t i = q[head++]; for (vid_t c : pchild[i]) { plevel[c] = plevel[i] + 1; q.push_back(c); } }
    }

    // SP-tree interval labeling (post-order over the tree rooted at virtual root K)
    ib_.assign(K, 0); ie_.assign(K, 0);
    {
        vid_t counter = 0;
        std::vector<std::pair<vid_t, std::size_t>> st;
        st.push_back({K, 0});
        // iterative: assign begin at entry, end at exit
        std::vector<vid_t> ibtmp(K + 1, 0), ietmp(K + 1, 0);
        std::vector<char> entered(K + 1, 0);
        while (!st.empty()) {
            auto& f = st.back();
            if (!entered[f.first]) { entered[f.first] = 1; ibtmp[f.first] = counter; }
            if (f.second < pchild[f.first].size()) {
                vid_t c = pchild[f.first][f.second++];
                st.push_back({c, 0});
            } else {
                ietmp[f.first] = counter++;
                st.pop_back();
            }
        }
        for (vid_t p = 0; p < K; ++p) { ib_[p] = ibtmp[p]; ie_[p] = ietmp[p]; }
    }

    // Step 4: cover adjacency (next-on-path first, then SP-tree cross-edges) + DFS X labeling
    std::vector<std::vector<vid_t>> covadj(n_);
    for (vid_t v = 0; v < n_; ++v) {
        vid_t i = pid_[v];
        if (sid[v] + 1 < (vid_t)paths[i].size()) covadj[v].push_back(paths[i][sid[v] + 1]);
        for (const vid_t* it = dag.out_begin(v); it != dag.out_end(v); ++it) {
            vid_t w = *it, j = pid_[w];
            if (j != i && ppar[j] == i) covadj[v].push_back(w);   // SP-tree cover cross-edge
        }
    }
    {
        std::vector<vid_t> paths_by_level(K);
        for (vid_t p = 0; p < K; ++p) paths_by_level[p] = p;
        std::sort(paths_by_level.begin(), paths_by_level.end(),
                  [&](vid_t a, vid_t b){ return plevel[a] < plevel[b]; });
        vid_t N = n_;
        std::vector<char> vis(n_, 0);
        std::vector<std::pair<vid_t, std::size_t>> st;
        for (vid_t p : paths_by_level) {
            vid_t s = paths[p][0];
            if (vis[s]) continue;
            vis[s] = 1; st.push_back({s, 0});
            while (!st.empty()) {
                auto& f = st.back();
                if (f.second < covadj[f.first].size()) {
                    vid_t w = covadj[f.first][f.second++];
                    if (!vis[w]) { vis[w] = 1; st.push_back({w, 0}); }
                } else {
                    x_[f.first] = N--;
                    st.pop_back();
                }
            }
        }
    }

    // Step 5: residual transitive closure Rc (Algorithm 3) in reverse topological order
    for (std::size_t i = topo.size(); i-- > 0;) {
        vid_t u = topo[i];
        std::vector<vid_t>& R = rc_[u];
        for (const vid_t* it = dag.out_begin(u); it != dag.out_end(u); ++it) {
            vid_t s = *it;
            // candidates: each successor s and its residual reps
            for (std::size_t z = 0; z <= rc_[s].size(); ++z) {
                vid_t w = (z == rc_[s].size()) ? s : rc_[s][z];
                if (cover_reach(u, w)) continue;            // already covered by the path-tree
                bool redundant = false;
                for (vid_t xx : R) if (cover_reach(xx, w)) { redundant = true; break; }
                if (redundant) continue;
                R.erase(std::remove_if(R.begin(), R.end(),
                          [&](vid_t xx){ return cover_reach(w, xx); }), R.end());
                R.push_back(w);
            }
        }
    }
}

bool PathTree::query(vid_t u, vid_t v) const {
    if (u == v) return true;
    if (cover_reach(u, v)) return true;
    for (vid_t x : rc_[u]) if (cover_reach(x, v)) return true;
    return false;
}

std::size_t PathTree::index_size_bytes() const {
    std::size_t b = (pid_.size() + x_.size()) * sizeof(vid_t) + (ib_.size() + ie_.size()) * sizeof(vid_t);
    for (const auto& r : rc_) b += r.size() * sizeof(vid_t);
    return b;
}

}  // namespace reachability
