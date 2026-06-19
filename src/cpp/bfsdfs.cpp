#include "reachability/bfsdfs.hpp"
#include <vector>
#include <queue>

namespace reachability {

bool bfs_reaches(const CSRGraph& g, vid_t u, vid_t v) {
    if (u == v) return true;                 // reflexive
    std::vector<char> seen(g.num_nodes(), 0);
    std::queue<vid_t> q;
    seen[u] = 1; q.push(u);
    while (!q.empty()) {
        vid_t x = q.front(); q.pop();
        for (const vid_t* it = g.out_begin(x); it != g.out_end(x); ++it) {
            vid_t w = *it;
            if (w == v) return true;
            if (!seen[w]) { seen[w] = 1; q.push(w); }
        }
    }
    return false;
}

}  // namespace reachability
