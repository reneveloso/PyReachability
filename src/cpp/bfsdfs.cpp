#include "reachability/bfsdfs.hpp"
#include <vector>
#include <queue>

namespace reachability {

// Plain breadth-first search from u, reporting whether v is encountered. O(V + E)
// per query, O(V) extra memory for the visited set.
bool bfs_reaches(const CSRGraph& g, vid_t u, vid_t v) {
    if (u == v) return true;                 // reachability is reflexive

    std::vector<char> seen(g.num_nodes(), 0);
    std::queue<vid_t> q;
    seen[u] = 1; q.push(u);
    while (!q.empty()) {
        vid_t x = q.front(); q.pop();
        for (const vid_t* it = g.out_begin(x); it != g.out_end(x); ++it) {
            vid_t w = *it;
            if (w == v) return true;         // found v: stop early
            if (!seen[w]) { seen[w] = 1; q.push(w); }
        }
    }
    return false;                            // exhausted u's reachable set without hitting v
}

}  // namespace reachability
