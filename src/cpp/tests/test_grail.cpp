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

TEST_CASE("grail topological levels (longest path from a root)") {
    // chain 0->1->2->3 plus a shortcut 0->3
    std::vector<vid_t> s{0,1,2,0}, d{1,2,3,3};
    CSRGraph g(4, s, d);
    Grail idx; idx.build(g, 2, 1);
    CHECK(idx.top_level(0) == 0);
    CHECK(idx.top_level(1) == 1);
    CHECK(idx.top_level(2) == 2);
    CHECK(idx.top_level(3) == 3);   // longest path 0->1->2->3, not the 0->3 shortcut
}

TEST_CASE("grail PP cuts are sound in both directions") {
    std::vector<vid_t> s{0,0,1,2,2}, d{1,2,3,3,4};
    CSRGraph g(5, s, d);
    Grail idx; idx.build(g, 5, 1);
    int pos = 0, neg = 0;
    for (vid_t u = 0; u < 5; ++u)
        for (vid_t v = 0; v < 5; ++v) {
            int r = idx.contains_pp(u, v);
            if (r == 1) { CHECK(bfs(g, u, v)); ++pos; }      // positive => truly reachable
            if (r == -1) { CHECK(!bfs(g, u, v)); ++neg; }    // negative => truly unreachable
        }
    CHECK(pos > 0);   // the positive cut must actually fire
    CHECK(neg > 0);
}

TEST_CASE("grail reaches matches brute force on a dag") {
    std::vector<vid_t> s{0,0,1,2,2}, d{1,2,3,3,4};
    CSRGraph g(5, s, d);
    Grail idx; idx.build(g, 5, 1);
    for (vid_t u = 0; u < 5; ++u)
        for (vid_t v = 0; v < 5; ++v)
            CHECK(idx.reaches(u, v) == bfs(g, u, v));
}

TEST_CASE("grail bidirectional matches brute force") {
    {
        std::vector<vid_t> s{0,0,1,2,2}, d{1,2,3,3,4};
        CSRGraph g(5, s, d);
        Grail idx; idx.build(g, 5, 1, /*bidirectional=*/true);
        for (vid_t u = 0; u < 5; ++u)
            for (vid_t v = 0; v < 5; ++v)
                CHECK(idx.reaches(u, v) == bfs(g, u, v));
    }
    {   // wide DAG with multiple paths to a sink
        std::vector<vid_t> s{0,0,0,1,2,3}, d{1,2,3,4,4,4};
        CSRGraph g(5, s, d);
        Grail idx; idx.build(g, 3, 7, true);
        for (vid_t u = 0; u < 5; ++u)
            for (vid_t v = 0; v < 5; ++v)
                CHECK(idx.reaches(u, v) == bfs(g, u, v));
    }
}

TEST_CASE("grail reaches on a chain and a wide dag") {
    { std::vector<vid_t> s{0,1,2,3}, d{1,2,3,4}; CSRGraph g(5, s, d);
      Grail idx; idx.build(g, 3, 7);
      for (vid_t u=0; u<5; ++u) for (vid_t v=0; v<5; ++v)
          CHECK(idx.reaches(u,v) == bfs(g,u,v)); }
    { std::vector<vid_t> s{0,0,0,1,2,3}, d{1,2,3,4,4,4}; CSRGraph g(5, s, d);
      Grail idx; idx.build(g, 2, 99);
      for (vid_t u=0; u<5; ++u) for (vid_t v=0; v<5; ++v)
          CHECK(idx.reaches(u,v) == bfs(g,u,v)); }
}
