#include "reachability/ferrari.hpp"
#include "reachability/levels.hpp"
#include <algorithm>
#include <numeric>
#include <vector>

namespace reachability {

namespace {
struct Iv { vid_t a, b; char ex; };
}  // namespace

void Ferrari::build(const CSRGraph& dag, int k) {
    if (k < 1) k = 1;
    n_ = dag.num_nodes();
    fwd_ = dag;
    level_ = topological_levels(dag);
    pi_.assign(n_, 0);
    is_.assign(n_, {}); ie_.assign(n_, {}); iex_.assign(n_, {});
    stamp_.assign(n_, 0); query_cnt_ = 0;
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

    // spanning forest (DFS tree) + post-order numbering: pi (post number), lo (subtree min)
    std::vector<vid_t> parent(n_, -1), lo(n_, 0);
    std::vector<std::vector<vid_t>> children(n_);
    {
        std::vector<char> seen(n_, 0);
        std::vector<vid_t> st;
        for (vid_t s : topo) {
            if (seen[s]) continue;
            seen[s] = 1; st.push_back(s);
            while (!st.empty()) {
                vid_t u = st.back(); st.pop_back();
                for (const vid_t* it = dag.out_begin(u); it != dag.out_end(u); ++it)
                    if (!seen[*it]) { seen[*it] = 1; parent[*it] = u; children[u].push_back(*it); st.push_back(*it); }
            }
        }
        vid_t counter = 0;
        std::vector<vid_t> sz(n_, 1);
        std::vector<std::pair<vid_t, std::size_t>> dst;
        for (vid_t r = 0; r < n_; ++r) {
            if (parent[r] != -1) continue;
            dst.push_back({r, 0});
            while (!dst.empty()) {
                auto& fr = dst.back();
                if (fr.second < children[fr.first].size()) dst.push_back({children[fr.first][fr.second++], 0});
                else {
                    vid_t v = fr.first;
                    pi_[v] = counter++;
                    lo[v] = pi_[v] - (sz[v] - 1);
                    if (parent[v] != -1) sz[parent[v]] += sz[v];
                    dst.pop_back();
                }
            }
        }
    }

    // reverse topological order: merge children's interval sets, then reduce to k intervals
    for (std::size_t i = topo.size(); i-- > 0;) {
        vid_t v = topo[i];
        std::vector<Iv> cur;
        cur.push_back({lo[v], pi_[v], 1});                 // tree interval (exact)
        for (const vid_t* it = dag.out_begin(v); it != dag.out_end(v); ++it) {
            vid_t c = *it;
            for (std::size_t j = 0; j < is_[c].size(); ++j)
                cur.push_back({is_[c][j], ie_[c][j], iex_[c][j]});
        }
        std::sort(cur.begin(), cur.end(), [](const Iv& x, const Iv& y){ return x.a < y.a || (x.a == y.a && x.b < y.b); });

        // coalesce overlapping / adjacent intervals (gap-free => stays exact iff all pieces exact)
        std::vector<Iv> m;
        for (const Iv& iv : cur) {
            if (!m.empty() && iv.a <= m.back().b + 1) {
                if (iv.b > m.back().b) m.back().b = iv.b;
                m.back().ex = (char)(m.back().ex && iv.ex);
            } else m.push_back(iv);
        }

        // reduce to k intervals: keep the k-1 largest gaps as separators, merge the rest
        if ((int)m.size() > k) {
            const vid_t N = (vid_t)m.size();
            std::vector<vid_t> gi(N - 1);
            std::iota(gi.begin(), gi.end(), 0);
            std::sort(gi.begin(), gi.end(), [&](vid_t x, vid_t y){
                long long gx = (long long)m[x + 1].a - m[x].b - 1, gy = (long long)m[y + 1].a - m[y].b - 1;
                return gx > gy;
            });
            std::vector<char> cut(N - 1, 0);
            for (int c = 0; c < k - 1; ++c) cut[gi[c]] = 1;   // separators
            std::vector<Iv> r;
            vid_t a = 0;
            while (a < N) {
                vid_t b = a;
                while (b < N - 1 && !cut[b]) ++b;             // extend group until a separator
                r.push_back({m[a].a, m[b].b, (char)(a == b ? m[a].ex : 0)});
                a = b + 1;
            }
            m.swap(r);
        }

        is_[v].reserve(m.size()); ie_[v].reserve(m.size()); iex_[v].reserve(m.size());
        for (const Iv& iv : m) { is_[v].push_back(iv.a); ie_[v].push_back(iv.b); iex_[v].push_back(iv.ex); }
    }
}

int Ferrari::check(vid_t v, vid_t pid) const {
    const std::vector<vid_t>& s = is_[v];
    // largest interval start <= pid
    std::size_t lo = 0, hi = s.size();
    while (lo < hi) { std::size_t mid = (lo + hi) / 2; if (s[mid] <= pid) lo = mid + 1; else hi = mid; }
    if (lo == 0) return 0;
    std::size_t idx = lo - 1;
    if (pid <= ie_[v][idx]) return iex_[v][idx] ? 2 : 1;
    return 0;
}

bool Ferrari::reaches(vid_t s, vid_t t) {
    if (s == t) return true;
    if (level_[s] >= level_[t]) return false;       // topological negative cut
    int r = check(s, pi_[t]);
    if (r == 0) return false;
    if (r == 2) return true;

    // approximate: guided DFS over out-neighbours
    ++query_cnt_;
    const int qc = query_cnt_;
    std::vector<vid_t> st;
    st.push_back(s); stamp_[s] = qc;
    while (!st.empty()) {
        vid_t x = st.back(); st.pop_back();
        for (const vid_t* it = fwd_.out_begin(x); it != fwd_.out_end(x); ++it) {
            vid_t c = *it;
            if (c == t) return true;
            if (stamp_[c] == qc) continue;
            if (level_[c] >= level_[t]) continue;   // cannot reach t
            int rc = check(c, pi_[t]);
            if (rc == 2) return true;
            if (rc == 0) continue;                  // t outside c's intervals -> prune
            stamp_[c] = qc; st.push_back(c);
        }
    }
    return false;
}

std::size_t Ferrari::index_size_bytes() const {
    std::size_t b = (pi_.size() + level_.size()) * sizeof(vid_t);
    for (vid_t v = 0; v < n_; ++v)
        b += is_[v].size() * (2 * sizeof(vid_t) + sizeof(char));
    return b;
}

}  // namespace reachability
