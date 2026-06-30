#include "reachability/pathhop.hpp"
#include "reachability/optimal_tree.hpp"
#include <algorithm>
#include <vector>

namespace reachability {

namespace {
void sort_unique(std::vector<vid_t>& v) {
    std::sort(v.begin(), v.end());
    v.erase(std::unique(v.begin(), v.end()), v.end());
}
}  // namespace

void PathHop::build(const CSRGraph& dag) {
    n_ = dag.num_nodes();
    parent_.assign(n_, -1); lo_.assign(n_, 0); hi_.assign(n_, 0);
    lout_.assign(n_, {}); lin_.assign(n_, {});
    if (n_ == 0) return;

    // topological order (Kahn)
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

    // tree cover = Agrawal's optimum tree cover (minimises the residual transitive closure)
    parent_ = optimal_tree_parent(dag);
    std::vector<std::vector<vid_t>> children(n_);
    for (vid_t v = 0; v < n_; ++v) if (parent_[v] != -1) children[parent_[v]].push_back(v);

    // interval labels via iterative post-order: hi = post number, lo = hi - subtree_size + 1
    {
        vid_t counter = 0;
        std::vector<std::pair<vid_t, std::size_t>> st;   // (vertex, child cursor)
        std::vector<vid_t> sz(n_, 1);
        for (vid_t r = 0; r < n_; ++r) {
            if (parent_[r] != -1) continue;              // roots only
            st.push_back({r, 0});
            while (!st.empty()) {
                auto& fr = st.back();
                if (fr.second < children[fr.first].size()) {
                    vid_t c = children[fr.first][fr.second++];
                    st.push_back({c, 0});
                } else {
                    vid_t v = fr.first;
                    hi_[v] = counter++;
                    lo_[v] = hi_[v] - (sz[v] - 1);
                    if (parent_[v] != -1) sz[parent_[v]] += sz[v];
                    st.pop_back();
                }
            }
        }
    }

    // residual TC: S(u) = maximal reachable subtree roots (antichain), Succ(u) = S(u) \ {u}
    std::vector<std::vector<vid_t>> S(n_);
    for (std::size_t i = topo.size(); i-- > 0;) {
        vid_t u = topo[i];
        std::vector<vid_t>& Su = S[u];
        Su.push_back(u);
        for (const vid_t* it = dag.out_begin(u); it != dag.out_end(u); ++it) {
            for (vid_t r : S[*it]) {
                bool dominated = false;
                for (std::size_t k = 0; k < Su.size();) {
                    if (anc(Su[k], r)) { dominated = true; break; }   // r in subtree of existing root
                    if (anc(r, Su[k])) { Su[k] = Su.back(); Su.pop_back(); }  // r dominates existing
                    else ++k;
                }
                if (!dominated) Su.push_back(r);
            }
        }
    }
    std::vector<std::vector<vid_t>> succ(n_), pred(n_);
    for (vid_t u = 0; u < n_; ++u)
        for (vid_t r : S[u]) if (r != u) { succ[u].push_back(r); pred[r].push_back(u); }

    // residual TC pairs (u, r), r in Succ(u)
    std::vector<std::pair<vid_t, vid_t>> R;
    for (vid_t u = 0; u < n_; ++u) for (vid_t r : succ[u]) R.emplace_back(u, r);
    if (R.empty()) return;

    auto in_succ = [&](vid_t a, vid_t b)->bool {   // b in Succ(a)?
        const std::vector<vid_t>& s = succ[a];
        return std::find(s.begin(), s.end(), b) != s.end();
    };

    // candidate path-hops: (x, y) with y a tree-descendant of x (Iy subset Ix), incl. y == x
    std::vector<std::pair<vid_t, vid_t>> hops;
    for (vid_t x = 0; x < n_; ++x)
        for (vid_t y = 0; y < n_; ++y)
            if (anc(x, y) && (!pred[x].empty() || !succ[y].empty() || x == y))
                hops.emplace_back(x, y);

    // greedy set cover by simplified hop density = |E(x;y) cap R| / (|Pred(x)| + |Succ(y)|)
    std::vector<char> uncov(R.size(), 1);
    long long remaining = (long long)R.size();
    auto covers = [&](vid_t x, vid_t y, vid_t u, vid_t v)->bool {
        // (u,v) in R (v in Succ(u)); E(x;y): type1 (u in Pred(x)U{x,y}, v in Succ(y)); type2 (u in Pred(x), v==x)
        bool uPred = in_succ(u, x);             // u in Pred(x) iff x in Succ(u)
        if (uPred && v == x) return true;       // type 2
        bool uSet = uPred || u == x || u == y;
        return uSet && in_succ(y, v);           // type 1 (v in Succ(y))
    };
    while (remaining > 0) {
        double bestD = -1.0; vid_t bx = -1, by = -1;
        for (auto& hp : hops) {
            vid_t x = hp.first, y = hp.second;
            long long w = (long long)pred[x].size() + (long long)succ[y].size();
            if (w == 0) continue;
            long long cov = 0;
            for (std::size_t pi = 0; pi < R.size(); ++pi)
                if (uncov[pi] && covers(x, y, R[pi].first, R[pi].second)) ++cov;
            if (cov == 0) continue;
            double d = (double)cov / w;
            if (d > bestD) { bestD = d; bx = x; by = y; }
        }
        if (bx < 0) break;   // safety

        for (vid_t a : pred[bx]) lout_[a].push_back(bx);
        for (vid_t d : succ[by]) {
            bool red = false;                              // skip if Lin(d) already has a tree-descendant of y
            for (vid_t w : lin_[d]) if (anc(by, w)) { red = true; break; }
            if (!red) lin_[d].push_back(by);
        }
        for (std::size_t pi = 0; pi < R.size(); ++pi)
            if (uncov[pi] && covers(bx, by, R[pi].first, R[pi].second)) { uncov[pi] = 0; --remaining; }
    }

    for (vid_t v = 0; v < n_; ++v) { sort_unique(lout_[v]); sort_unique(lin_[v]); }
}

bool PathHop::query(vid_t u, vid_t v) const {
    if (u == v) return true;
    if (anc(u, v)) return true;                  // tree reachability (Iv subset Iu)

    // In_v = {v} U Lin(v) U Lin(z) for all tree ancestors z of v
    std::vector<vid_t> inv;
    inv.push_back(v);
    for (vid_t z = v; z != -1; z = parent_[z])
        inv.insert(inv.end(), lin_[z].begin(), lin_[z].end());

    // Out_u = {u} U Lout(u); reachable iff some x in Out_u is a tree-ancestor of some y in In_v
    for (vid_t y : inv) if (anc(u, y)) return true;     // x = u
    for (vid_t x : lout_[u])
        for (vid_t y : inv) if (anc(x, y)) return true;
    return false;
}

std::size_t PathHop::index_size_bytes() const {
    std::size_t b = (parent_.size() + lo_.size() + hi_.size()) * sizeof(vid_t);
    for (const auto& l : lout_) b += l.size() * sizeof(vid_t);
    for (const auto& l : lin_) b += l.size() * sizeof(vid_t);
    return b;
}

}  // namespace reachability
