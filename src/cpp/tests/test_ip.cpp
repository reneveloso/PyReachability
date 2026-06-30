#include "doctest.h"
#include "reachability/ip.hpp"
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

TEST_CASE("IP matches brute force on dags for several params") {
    std::vector<std::pair<std::vector<vid_t>, std::vector<vid_t>>> graphs = {
        {{0,0,1,2,2}, {1,2,3,3,4}},
        {{0,1,2,3,0}, {1,2,3,4,4}},
        {{0,0,0,1,2,3}, {1,2,3,4,4,4}},
        {{0,1,2,3}, {1,2,3,4}},
        {{0,0,1,1,2,3}, {1,2,3,4,4,4}},
    };
    for (int k : {1, 2}) for (int np : {1, 3}) {
        for (auto& gr : graphs) {
            vid_t n = 5;
            CSRGraph g(n, gr.first, gr.second);
            IP idx; idx.build(g, k, np, 1);
            for (vid_t u = 0; u < n; ++u)
                for (vid_t v = 0; v < n; ++v)
                    CHECK(idx.reaches(u, v) == bfs(g, u, v));
        }
    }
    CSRGraph g(5, graphs[0].first, graphs[0].second);
    IP idx; idx.build(g, 2, 2, 1);
    CHECK(idx.index_size_bytes() > 0);
}

TEST_CASE("IP handles empty and disconnected graphs") {
    CSRGraph empty(0, {}, {});
    IP e; e.build(empty, 2, 2, 1);

    CSRGraph iso(4, {}, {});
    IP idx; idx.build(iso, 2, 2, 1);
    for (vid_t u = 0; u < 4; ++u)
        for (vid_t v = 0; v < 4; ++v)
            CHECK(idx.reaches(u, v) == (u == v));
}
