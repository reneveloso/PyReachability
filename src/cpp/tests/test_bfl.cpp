#include "doctest.h"
#include "reachability/bfl.hpp"
#include "reachability/csr_graph.hpp"
#include <vector>
#include <queue>
using namespace reachability;

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

TEST_CASE("bfl matches brute force on dags") {
    std::vector<std::pair<std::vector<vid_t>, std::vector<vid_t>>> graphs = {
        {{0,0,1,2,2}, {1,2,3,3,4}},
        {{0,1,2,3,0}, {1,2,3,4,4}},
        {{0,0,0,1,2,3}, {1,2,3,4,4,4}},
    };
    for (auto& gr : graphs) {
        CSRGraph g(5, gr.first, gr.second);
        BFL idx; idx.build(g, 5, 1);
        for (vid_t u = 0; u < 5; ++u)
            for (vid_t v = 0; v < 5; ++v)
                CHECK(idx.reaches(u, v) == bfs(g, u, v));
    }
    CSRGraph g(5, graphs[0].first, graphs[0].second);
    BFL idx; idx.build(g, 5, 1);
    CHECK(idx.index_size_bytes() > 0);
}

TEST_CASE("bfl bloom cuts are sound (never claim unreachable for reachable)") {
    std::vector<vid_t> s{0,0,1,2,2}, d{1,2,3,3,4};
    CSRGraph g(5, s, d);
    BFL idx; idx.build(g, 5, 1);
    // exhaustive: result must equal BFS for several seeds/k
    for (int k : {1, 3, 5}) {
        BFL i2; i2.build(g, k, 7);
        for (vid_t u = 0; u < 5; ++u)
            for (vid_t v = 0; v < 5; ++v)
                CHECK(i2.reaches(u, v) == bfs(g, u, v));
    }
}
