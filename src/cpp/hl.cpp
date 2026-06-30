#include "reachability/hl.hpp"
#include "reachability/levels.hpp"
#include <algorithm>
#include <vector>

namespace reachability {

namespace {
void sort_unique(std::vector<vid_t>& v) {
    std::sort(v.begin(), v.end());
    v.erase(std::unique(v.begin(), v.end()), v.end());
}
}  // namespace

void HL::build(const CSRGraph& dag, int eps) {
    if (eps < 1) eps = 1;
    n_ = dag.num_nodes();
    L_.resize(n_);
    level_ = topological_levels(dag);
    if (n_ == 0) return;
    const int half = (eps + 1) / 2;   // ceil(eps/2)

    // current folding graph G_i adjacency (only `incur` vertices are valid)
    std::vector<std::vector<vid_t>> co(n_), ci(n_);
    for (vid_t u = 0; u < n_; ++u)
        for (const vid_t* it = dag.out_begin(u); it != dag.out_end(u); ++it) { co[u].push_back(*it); ci[*it].push_back(u); }
    std::vector<vid_t> curlist(n_);
    for (vid_t v = 0; v < n_; ++v) curlist[v] = v;
    std::vector<char> incur(n_, 1);

    std::vector<vid_t> hlevel(n_, -1);
    std::vector<std::vector<vid_t>> nout(n_), nin(n_), bout(n_), bin(n_);

    // BFS over `adj` (restricted to incur) from s, up to depth D; returns (vertex, dist) pairs.
    std::vector<int> dist(n_, -1);
    auto bfs = [&](const std::vector<std::vector<vid_t>>& adj, vid_t s, int D,
                   std::vector<std::pair<vid_t, int>>& out) {
        out.clear(); dist[s] = 0; out.push_back({s, 0});
        std::vector<vid_t> q{s}; std::size_t h = 0;
        while (h < q.size()) {
            vid_t x = q[h++]; int dx = dist[x];
            if (dx == D) continue;
            for (vid_t w : adj[x]) if (incur[w] && dist[w] < 0) { dist[w] = dx + 1; out.push_back({w, dx + 1}); q.push_back(w); }
        }
        for (auto& pr : out) dist[pr.first] = -1;   // reset for next call
    };
    std::vector<std::pair<vid_t, int>> bf, bf2;

    int i = 0;
    std::vector<vid_t> coreList;
    for (;;) {
        // ---- FastCover (SCARAB): backbone star covers every distance-eps pair via a member ----
        std::vector<char> instar(n_, 0);
        std::vector<vid_t> order = curlist;
        std::sort(order.begin(), order.end(), [&](vid_t a, vid_t b) {
            long long da = (long long)(co[a].size() + 1) * (ci[a].size() + 1);
            long long db = (long long)(co[b].size() + 1) * (ci[b].size() + 1);
            return da != db ? da > db : a < b;
        });
        for (vid_t u : order) {
            bfs(co, u, eps, bf);
            std::vector<vid_t> Seps, M;
            for (auto& pr : bf) {
                if (pr.second == eps) Seps.push_back(pr.first);
                if (instar[pr.first] && pr.second <= eps) M.push_back(pr.first);
            }
            bool covered = true;
            if (!Seps.empty()) {
                std::vector<vid_t> reach;
                for (vid_t x : M) { bfs(co, x, eps, bf2); for (auto& pr : bf2) reach.push_back(pr.first); }
                sort_unique(reach);
                for (vid_t v : Seps) if (!std::binary_search(reach.begin(), reach.end(), v)) { covered = false; break; }
            }
            if (!covered) instar[u] = 1;
        }
        std::vector<vid_t> star;
        for (vid_t v : curlist) if (instar[v]) star.push_back(v);

        if (star.size() == curlist.size() || star.empty()) {   // no shrink -> this is the core
            for (vid_t v : curlist) hlevel[v] = i;
            coreList = curlist;
            break;
        }

        // ---- finalize the removed (level-i) vertices: N^half neighbours + B^eps backbone sets ----
        for (vid_t v : curlist) {
            if (instar[v]) continue;
            hlevel[v] = i;
            bfs(co, v, half, bf); for (auto& pr : bf) if (pr.second >= 1) nout[v].push_back(pr.first);
            bfs(ci, v, half, bf); for (auto& pr : bf) if (pr.second >= 1) nin[v].push_back(pr.first);
            // B^eps_out: backbone within eps, keep only the nearest (drop u if another backbone x reaches u within eps)
            bfs(co, v, eps, bf);
            std::vector<vid_t> cand;
            for (auto& pr : bf) if (pr.first != v && instar[pr.first]) cand.push_back(pr.first);
            std::vector<vid_t> keepO;
            {
                std::vector<char> isCand(n_, 0); for (vid_t x : cand) isCand[x] = 1;
                std::vector<char> dom(n_, 0);
                for (vid_t x : cand) { bfs(co, x, eps, bf2); for (auto& pr : bf2) if (pr.first != x && isCand[pr.first]) dom[pr.first] = 1; }
                for (vid_t x : cand) if (!dom[x]) keepO.push_back(x);
            }
            bout[v] = keepO;
            bfs(ci, v, eps, bf);
            std::vector<vid_t> candI;
            for (auto& pr : bf) if (pr.first != v && instar[pr.first]) candI.push_back(pr.first);
            std::vector<vid_t> keepI;
            {
                std::vector<char> isCand(n_, 0); for (vid_t x : candI) isCand[x] = 1;
                std::vector<char> dom(n_, 0);
                for (vid_t x : candI) { bfs(ci, x, eps, bf2); for (auto& pr : bf2) if (pr.first != x && isCand[pr.first]) dom[pr.first] = 1; }
                for (vid_t x : candI) if (!dom[x]) keepI.push_back(x);
            }
            bin[v] = keepI;
        }

        // ---- build the backbone graph G_{i+1}: star vertices, edges within distance eps+1 ----
        std::vector<std::vector<vid_t>> no(n_), ni(n_);
        for (vid_t a : star) {
            bfs(co, a, eps + 1, bf);
            for (auto& pr : bf) if (pr.second >= 1 && instar[pr.first]) { no[a].push_back(pr.first); ni[pr.first].push_back(a); }
        }
        for (vid_t v : curlist) if (!instar[v]) incur[v] = 0;
        co.swap(no); ci.swap(ni);
        curlist.swap(star);
        ++i;
    }

    // ---- label the core graph with a vertex-id 2-hop (pruned landmark labeling, ascending-id order) ----
    // Self labels (s in Lin[s]/Lout[s]) are added by the BFS itself, not pre-seeded — pre-seeding
    // would make the root prune immediately and stop the traversal.
    {
        std::vector<vid_t> q(n_);
        std::vector<char> vis(n_, 0);
        for (vid_t s : coreList) {           // coreList is ascending id -> labels stay sorted
            vid_t qs = 0, qt = 0; q[qt++] = s; vis[s] = 1;     // forward BFS fills Lin
            while (qs != qt) { vid_t v = q[qs++];
                if (two_hop_intersects(L_, s, v)) continue;
                L_.Lin[v].push_back(s);
                for (vid_t w : co[v]) if (incur[w] && !vis[w]) { vis[w] = 1; q[qt++] = w; } }
            for (vid_t z = 0; z < qt; ++z) vis[q[z]] = 0;
            qs = qt = 0; q[qt++] = s; vis[s] = 1;              // backward BFS fills Lout
            while (qs != qt) { vid_t v = q[qs++];
                if (two_hop_intersects(L_, v, s)) continue;
                L_.Lout[v].push_back(s);
                for (vid_t w : ci[v]) if (incur[w] && !vis[w]) { vis[w] = 1; q[qt++] = w; } }
            for (vid_t z = 0; z < qt; ++z) vis[q[z]] = 0;
        }
    }

    // ---- propagate labels down (Formulas 4/5), level h-1 .. 0; backbone labels already done ----
    std::vector<std::vector<vid_t>> byl(i + 1);
    for (vid_t v = 0; v < n_; ++v) if (hlevel[v] >= 0 && hlevel[v] < i) byl[hlevel[v]].push_back(v);
    for (int lev = i - 1; lev >= 0; --lev) {
        for (vid_t v : byl[lev]) {
            std::vector<vid_t>& lo = L_.Lout[v];
            lo.push_back(v);
            for (vid_t w : nout[v]) lo.push_back(w);
            for (vid_t u : bout[v]) lo.insert(lo.end(), L_.Lout[u].begin(), L_.Lout[u].end());
            sort_unique(lo);
            std::vector<vid_t>& li = L_.Lin[v];
            li.push_back(v);
            for (vid_t w : nin[v]) li.push_back(w);
            for (vid_t u : bin[v]) li.insert(li.end(), L_.Lin[u].begin(), L_.Lin[u].end());
            sort_unique(li);
        }
    }
    for (vid_t v = 0; v < n_; ++v) { sort_unique(L_.Lout[v]); sort_unique(L_.Lin[v]); }
}

bool HL::query(vid_t u, vid_t v) const {
    if (u == v) return true;
    if (level_[u] >= level_[v]) return false;
    return two_hop_intersects(L_, u, v);
}

std::size_t HL::index_size_bytes() const {
    return L_.size_bytes() + level_.size() * sizeof(vid_t);
}

}  // namespace reachability
