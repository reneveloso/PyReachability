#define DOCTEST_CONFIG_IMPLEMENT_WITH_MAIN
#include "doctest.h"
#include "reachability/csr_graph.hpp"
#include <vector>
using reachability::CSRGraph;
using reachability::vid_t;

TEST_CASE("csr basic structure") {
    std::vector<vid_t> src{0, 0, 1, 2};
    std::vector<vid_t> dst{1, 2, 2, 0};
    CSRGraph g(3, src, dst);
    CHECK(g.num_nodes() == 3);
    CHECK(g.num_edges() == 4);
    CHECK(g.out_degree(0) == 2);
    std::vector<vid_t> nbrs(g.out_begin(0), g.out_end(0));
    CHECK(nbrs == std::vector<vid_t>{1, 2});
}

TEST_CASE("csr deduplicates duplicate edges and drops self-loops") {
    std::vector<vid_t> src{0, 0, 0, 1};
    std::vector<vid_t> dst{1, 1, 0, 1};   // dup (0,1); self-loops (0,0) and (1,1)
    CSRGraph g(2, src, dst);
    CHECK(g.num_edges() == 1);
    CHECK(g.out_degree(0) == 1);
    CHECK(*g.out_begin(0) == 1);
    CHECK(g.out_degree(1) == 0);
}

TEST_CASE("empty graph") {
    CSRGraph g(3, {}, {});
    CHECK(g.num_nodes() == 3);
    CHECK(g.num_edges() == 0);
    CHECK(g.out_degree(2) == 0);
}
