#include "doctest.h"
#include "reachability/scc.hpp"
#include "reachability/csr_graph.hpp"
#include <vector>
#include <set>
using namespace reachability;

TEST_CASE("scc collapses a cycle") {
    // 0->1->2->0 is one SCC; 2->3 separate; 3 alone.
    std::vector<vid_t> src{0, 1, 2, 2};
    std::vector<vid_t> dst{1, 2, 0, 3};
    CSRGraph g(4, src, dst);
    Condensation c = scc_condense(g);
    CHECK(c.num_comp == 2);
    CHECK(c.comp[0] == c.comp[1]);
    CHECK(c.comp[1] == c.comp[2]);
    CHECK(c.comp[0] != c.comp[3]);
    CHECK(c.dag.num_edges() == 1);          // one edge between the two components
}

TEST_CASE("scc on a dag is identity in component count") {
    std::vector<vid_t> src{0, 1};
    std::vector<vid_t> dst{1, 2};
    CSRGraph g(3, src, dst);
    Condensation c = scc_condense(g);
    CHECK(c.num_comp == 3);
    // topo order: a component appears before any it points to
    std::vector<int> pos(c.num_comp);
    for (int i = 0; i < c.num_comp; ++i) pos[c.topo_order[i]] = i;
    CHECK(pos[c.comp[0]] < pos[c.comp[1]]);
    CHECK(pos[c.comp[1]] < pos[c.comp[2]]);
}
