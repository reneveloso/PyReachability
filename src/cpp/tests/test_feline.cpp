#include "doctest.h"
#include "reachability/feline.hpp"
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

TEST_CASE("feline dominance is a necessary condition (no false negatives)") {
    // DAG from the paper's Fig.2-ish: 0->1->3, 0->2->3, 2->4
    std::vector<vid_t> s{0,0,1,2,2}, d{1,2,3,3,4};
    CSRGraph g(5, s, d);
    Feline idx; idx.build(g);
    for (vid_t u = 0; u < 5; ++u)
        for (vid_t v = 0; v < 5; ++v)
            if (bfs(g, u, v)) CHECK(idx.dominates(u, v));   // reachable => dominated
    // and the dominance cut must actually reject some unreachable pairs
    int cut = 0;
    for (vid_t u = 0; u < 5; ++u)
        for (vid_t v = 0; v < 5; ++v)
            if (!bfs(g, u, v) && !idx.dominates(u, v)) ++cut;
    CHECK(cut > 0);
}

TEST_CASE("feline reaches matches brute force") {
    {
        std::vector<vid_t> s{0,0,1,2,2}, d{1,2,3,3,4};
        CSRGraph g(5, s, d);
        Feline idx; idx.build(g);
        for (vid_t u = 0; u < 5; ++u)
            for (vid_t v = 0; v < 5; ++v)
                CHECK(idx.reaches(u, v) == bfs(g, u, v));
    }
    {   // chain + shortcut
        std::vector<vid_t> s{0,1,2,3,0}, d{1,2,3,4,4};
        CSRGraph g(5, s, d);
        Feline idx; idx.build(g);
        for (vid_t u = 0; u < 5; ++u)
            for (vid_t v = 0; v < 5; ++v)
                CHECK(idx.reaches(u, v) == bfs(g, u, v));
    }
    {   // wide DAG: many paths to a sink
        std::vector<vid_t> s{0,0,0,1,2,3}, d{1,2,3,4,4,4};
        CSRGraph g(5, s, d);
        Feline idx; idx.build(g);
        for (vid_t u = 0; u < 5; ++u)
            for (vid_t v = 0; v < 5; ++v)
                CHECK(idx.reaches(u, v) == bfs(g, u, v));
    }
}
