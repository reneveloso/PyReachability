#include "doctest.h"
#include "reachability/dynamic/query.hpp"

#include <algorithm>

using namespace reachability::dynamic;

// Builds 0 -> 1 -> 2 in E_DAG with coordinates consistent with that order.
static void chain_of_three(DynamicGraph& g, DynIndex& idx) {
    for (unsigned v = 0; v < 3; ++v) g.dag_add_vertex(v);
    g.dag_add_edge(0, 1);
    g.dag_add_edge(1, 2);
    idx.set_from_scratch({0, 1, 2}, {0, 1, 2});
}

TEST_CASE("dyn_reachable: follows a path, and refuses what has no path") {
    DynamicGraph g; DynIndex idx;
    chain_of_three(g, idx);
    CHECK(dyn_reachable(g, idx, 0, 2));
    CHECK(dyn_reachable(g, idx, 0, 0));   // reflexive
    CHECK_FALSE(dyn_reachable(g, idx, 2, 0));
}

TEST_CASE("reduced_rectangle: empty iff unreachable, else includes both ends") {
    DynamicGraph g; DynIndex idx;
    chain_of_three(g, idx);
    auto p = reduced_rectangle(g, idx, 0, 2);
    CHECK_FALSE(p.empty());
    CHECK(std::find(p.begin(), p.end(), 0u) != p.end());
    CHECK(std::find(p.begin(), p.end(), 2u) != p.end());
    CHECK(reduced_rectangle(g, idx, 2, 0).empty());
}
