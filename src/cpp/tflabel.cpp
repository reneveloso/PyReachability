#include "reachability/tflabel.hpp"
#include "reachability/levels.hpp"
#include <algorithm>
#include <numeric>
#include <vector>

namespace reachability {

namespace {
void sort_unique(std::vector<vid_t>& v) {
    std::sort(v.begin(), v.end());
    v.erase(std::unique(v.begin(), v.end()), v.end());
}
}  // namespace

void TFLabel::build(const CSRGraph& dag) {
    n_ = dag.num_nodes();
    L_.resize(n_);
    level_ = topological_levels(dag);   // 0-indexed longest path from a source
    if (n_ == 0) return;

    // 1-indexed level per vertex; vertex set grows with dummies for cross-level edges.
    std::vector<vid_t> lvl(n_);
    for (vid_t v = 0; v < n_; ++v) lvl[v] = level_[v] + 1;

    std::vector<std::vector<vid_t>> out(n_), in(n_);
    auto add_dummy = [&](vid_t at_level) -> vid_t {
        vid_t id = static_cast<vid_t>(lvl.size());
        lvl.push_back(at_level); out.emplace_back(); in.emplace_back();
        return id;
    };

    // Make the DAG level-consecutive (L-partite) by subdividing every cross-level edge:
    // an edge u -> v with lvl[v] > lvl[u]+1 becomes a dummy chain through each level between.
    for (vid_t u = 0; u < n_; ++u)
        for (const vid_t* it = dag.out_begin(u); it != dag.out_end(u); ++it) {
            vid_t v = *it;                      // lvl[v] > lvl[u] always holds
            if (lvl[v] == lvl[u] + 1) {
                out[u].push_back(v); in[v].push_back(u);
            } else {
                vid_t prev = u;
                for (vid_t L = lvl[u] + 1; L < lvl[v]; ++L) {
                    vid_t d = add_dummy(L);
                    out[prev].push_back(d); in[d].push_back(prev);
                    prev = d;
                }
                out[prev].push_back(v); in[v].push_back(prev);
            }
        }

    const vid_t N = static_cast<vid_t>(lvl.size());   // total incl. dummies

    // Topological folding. cl[v] = level within the current fold graph; halved each fold.
    // tf[v] = fold in which v is removed (its last folding graph). nbout/nbin = neighbours in
    // that last folding graph (all of strictly larger tf, by Lemma 5).
    std::vector<vid_t> tf(N, 0), cl(N);
    for (vid_t v = 0; v < N; ++v) cl[v] = lvl[v];
    std::vector<std::vector<vid_t>> nbout(N), nbin(N);
    std::vector<char> alive(N, 1);

    vid_t fold = 1;
    while (true) {
        vid_t M = 0;
        for (vid_t v = 0; v < N; ++v) if (alive[v] && cl[v] > M) M = cl[v];
        if (M <= 1) {                       // one level left: nothing more to fold
            for (vid_t v = 0; v < N; ++v) if (alive[v]) tf[v] = fold;
            break;
        }

        // Odd-level vertices are removed this fold; reconnect around them (in-nbr -> out-nbr).
        // An L-partite graph has edges only between consecutive levels, so every neighbour of
        // an odd-level vertex is at an even level (a survivor) and all survivor-survivor
        // reachability is captured by these shortcuts.
        std::vector<std::vector<vid_t>> nout(N), nin(N);
        for (vid_t v = 0; v < N; ++v) {
            if (!alive[v] || (cl[v] & 1) == 0) continue;
            tf[v] = fold;
            nbout[v] = out[v];
            nbin[v] = in[v];
            for (vid_t a : in[v])
                for (vid_t b : out[v]) { nout[a].push_back(b); nin[b].push_back(a); }
        }

        for (vid_t v = 0; v < N; ++v) {
            if (!alive[v]) continue;
            if (cl[v] & 1) alive[v] = 0;
            else cl[v] /= 2;
        }
        out.swap(nout); in.swap(nin);
        for (vid_t v = 0; v < N; ++v) if (alive[v]) { sort_unique(out[v]); sort_unique(in[v]); }
        ++fold;
    }

    // Label closure (Definition 5), processed in decreasing tf so dependencies are ready:
    //   labelout(v) = {v} | union of labelout(w) for w in nbout(v);  labelin symmetric.
    std::vector<vid_t> order(N);
    std::iota(order.begin(), order.end(), 0);
    std::sort(order.begin(), order.end(), [&](vid_t a, vid_t b){ return tf[a] > tf[b]; });

    std::vector<std::vector<vid_t>> lo(N), li(N);
    for (vid_t v : order) {
        std::vector<vid_t>& o = lo[v];
        o.push_back(v);
        for (vid_t w : nbout[v]) o.insert(o.end(), lo[w].begin(), lo[w].end());
        sort_unique(o);
        std::vector<vid_t>& i = li[v];
        i.push_back(v);
        for (vid_t w : nbin[v]) i.insert(i.end(), li[w].begin(), li[w].end());
        sort_unique(i);
    }

    for (vid_t v = 0; v < n_; ++v) { L_.Lout[v] = std::move(lo[v]); L_.Lin[v] = std::move(li[v]); }
}

bool TFLabel::query(vid_t u, vid_t v) const {
    if (u == v) return true;
    if (level_[u] >= level_[v]) return false;   // topological quick reject
    return two_hop_intersects(L_, u, v);
}

std::size_t TFLabel::index_size_bytes() const {
    return L_.size_bytes() + level_.size() * sizeof(vid_t);
}

}  // namespace reachability
