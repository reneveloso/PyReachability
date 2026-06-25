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

void HL::build(const CSRGraph& dag) {
    n_ = dag.num_nodes();
    L_.resize(n_);
    level_ = topological_levels(dag);
    if (n_ == 0) return;

    // current graph G_i adjacency (indexed by global vid; only curV entries used)
    std::vector<std::vector<vid_t>> cur_out(n_), cur_in(n_);
    for (vid_t u = 0; u < n_; ++u)
        for (const vid_t* it = dag.out_begin(u); it != dag.out_end(u); ++it) {
            cur_out[u].push_back(*it); cur_in[*it].push_back(u);
        }

    std::vector<vid_t> curV(n_);
    for (vid_t v = 0; v < n_; ++v) curV[v] = v;

    std::vector<vid_t> hlevel(n_, -1);
    std::vector<std::vector<vid_t>> my_out(n_), my_in(n_);  // adjacency at each vertex's own level

    vid_t i = 0;
    while (true) {
        // Greedy max-degree vertex cover of the current graph (eps=1 backbone).
        std::vector<char> incover(n_, 0);
        for (;;) {
            vid_t best = -1, bestdeg = 0;
            for (vid_t v : curV) {
                if (incover[v]) continue;
                vid_t d = 0;
                for (vid_t w : cur_out[v]) if (!incover[w]) ++d;
                for (vid_t w : cur_in[v])  if (!incover[w]) ++d;
                if (d > bestdeg) { bestdeg = d; best = v; }
            }
            if (bestdeg == 0) break;     // no uncovered edges remain
            incover[best] = 1;
        }

        std::vector<vid_t> nextV;
        for (vid_t v : curV) if (incover[v]) nextV.push_back(v);

        if (nextV.empty()) {             // edgeless core: assign this level and stop
            for (vid_t v : curV) hlevel[v] = i;
            break;
        }

        // Vertices excluded from the cover are finalized at level i with their G_i adjacency.
        for (vid_t v : curV)
            if (!incover[v]) {
                hlevel[v] = i;
                my_out[v] = cur_out[v];
                my_in[v] = cur_in[v];
            }

        // Build G_{i+1} among nextV: backbone pairs within distance <= 2 in G_i (eps+1).
        std::vector<char> innext(n_, 0);
        for (vid_t v : nextV) innext[v] = 1;
        std::vector<std::vector<vid_t>> next_out(n_), next_in(n_);
        for (vid_t a : nextV) {
            for (vid_t w : cur_out[a]) {
                if (innext[w]) { next_out[a].push_back(w); next_in[w].push_back(a); }
                for (vid_t x : cur_out[w])
                    if (innext[x] && x != a) { next_out[a].push_back(x); next_in[x].push_back(a); }
            }
        }
        for (vid_t a : nextV) { sort_unique(next_out[a]); sort_unique(next_in[a]); }

        // advance
        for (vid_t v : curV) if (!incover[v]) { cur_out[v].clear(); cur_in[v].clear(); }
        cur_out.swap(next_out); cur_in.swap(next_in);
        curV.swap(nextV);
        ++i;
    }
    const vid_t h = i;

    // Label from the core (level h) down to level 0; backbone neighbours are higher and ready.
    std::vector<std::vector<vid_t>> bylevel(h + 1);
    for (vid_t v = 0; v < n_; ++v) bylevel[hlevel[v]].push_back(v);

    for (vid_t lev = h; ; --lev) {
        for (vid_t v : bylevel[lev]) {
            std::vector<vid_t>& lo = L_.Lout[v];
            lo.push_back(v);
            for (vid_t w : my_out[v]) lo.insert(lo.end(), L_.Lout[w].begin(), L_.Lout[w].end());
            sort_unique(lo);
            std::vector<vid_t>& li = L_.Lin[v];
            li.push_back(v);
            for (vid_t w : my_in[v]) li.insert(li.end(), L_.Lin[w].begin(), L_.Lin[w].end());
            sort_unique(li);
        }
        if (lev == 0) break;
    }
}

bool HL::query(vid_t u, vid_t v) const {
    if (u == v) return true;
    if (level_[u] >= level_[v]) return false;   // topological quick reject
    return two_hop_intersects(L_, u, v);
}

std::size_t HL::index_size_bytes() const {
    return L_.size_bytes() + level_.size() * sizeof(vid_t);
}

}  // namespace reachability
