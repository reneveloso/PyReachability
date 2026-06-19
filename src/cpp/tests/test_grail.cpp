#include "doctest.h"
#include "reachability/grail.hpp"
#include "reachability/csr_graph.hpp"
#include <vector>
#include <queue>
using namespace reachability;

// brute-force reachability on the DAG, for cross-checking
static bool bfs(const CSRGraph& g, vid_t s, vid_t t) {
    if (s == t) return true;
    std::vector<char> seen(g.num_nodes(), 0);
    std::queue<vid_t> q; seen[s] = 1; q.push(s);
    while (!q.empty()) { vid_t x = q.front(); q.pop();
        for (const vid_t* it = g.out_begin(x); it != g.out_end(x); ++it) {
            if (*it == t) return true;
            if (!seen[*it]) { seen[*it] = 1; q.push(*it); } } }
    return false;
}

TEST_CASE("grail labels have no false negatives") {
    // DAG: 0->1->3, 0->2->3, 2->4
    std::vector<vid_t> s{0,0,1,2,2}, d{1,2,3,3,4};
    CSRGraph g(5, s, d);
    Grail idx; idx.build(g, 5, 1);
    CHECK(idx.dim() == 5);
    for (vid_t u = 0; u < 5; ++u)
        for (vid_t v = 0; v < 5; ++v)
            if (bfs(g, u, v)) CHECK(idx.contains(u, v));   // reachable => contained
    CHECK(idx.index_size_bytes() > 0);
}

TEST_CASE("grail contains rejects some unreachable pairs") {
    std::vector<vid_t> s{0,0,1,2,2}, d{1,2,3,3,4};
    CSRGraph g(5, s, d);
    Grail idx; idx.build(g, 5, 1);
    // 3 and 4 reach nothing; correct labels must cut at least one unreachable pair.
    int cut = 0;
    for (vid_t u = 0; u < 5; ++u)
        for (vid_t v = 0; v < 5; ++v)
            if (!bfs(g, u, v) && !idx.contains(u, v)) ++cut;
    CHECK(cut > 0);
}
