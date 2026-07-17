#include "doctest.h"
#include "reachability/dynamic/scc.hpp"

#include <algorithm>
#include <unordered_set>
#include <vector>

using reachability::dynamic::DynamicGraph;
using reachability::dynamic::reachable_within;
using reachability::dynamic::tarjan_within;
using reachability::dynamic::vertex_t;

TEST_CASE("tarjan_within: partitions the induced subgraph") {
    // Inside C = {0,1,2,3}: 0<->1 is an SCC; 2->3 are two singletons.
    DynamicGraph g;
    for (vertex_t v = 0; v < 4; ++v) g.add_vertex(v);
    g.add_edge(0, 1); g.add_edge(1, 0);
    g.add_edge(2, 3);

    std::vector<std::vector<vertex_t>> parts = tarjan_within(g, {0, 1, 2, 3});
    CHECK(parts.size() == 3);           // {0,1}, {2}, {3}

    size_t size_of_0 = 0, total = 0;
    for (const auto& p : parts) {
        total += p.size();
        if (std::find(p.begin(), p.end(), 0u) != p.end()) size_of_0 = p.size();
    }
    CHECK(total == 4);                  // every member appears exactly once
    CHECK(size_of_0 == 2);              // 0 and 1 land in the same partition
}

TEST_CASE("tarjan_within: an edge leaving the set cannot merge partitions") {
    // 0 and 1 are mutually reachable ONLY through vertex 9, which is outside C.
    // Restricted to C they must remain two separate partitions.
    DynamicGraph g;
    for (vertex_t v = 0; v < 2; ++v) g.add_vertex(v);
    g.add_vertex(9);
    g.add_edge(0, 9); g.add_edge(9, 1); g.add_edge(1, 9); g.add_edge(9, 0);

    std::vector<std::vector<vertex_t>> parts = tarjan_within(g, {0, 1});
    CHECK(parts.size() == 2);
}

TEST_CASE("reachable_within: the walk never leaves the set") {
    DynamicGraph g;
    for (vertex_t v = 0; v < 4; ++v) g.add_vertex(v);
    g.add_vertex(9);
    g.add_edge(0, 1); g.add_edge(1, 2);   // inside C
    g.add_edge(0, 9); g.add_edge(9, 3);   // detour that leaves C
    std::unordered_set<vertex_t> C{0, 1, 2, 3};

    CHECK(reachable_within(g, C, 0, 2));        // 0->1->2 stays inside C
    CHECK_FALSE(reachable_within(g, C, 0, 3));  // the path through 9 is not allowed
    CHECK(reachable_within(g, C, 2, 2));        // reflexive
    CHECK_FALSE(reachable_within(g, C, 2, 0));  // no reverse path
    CHECK_FALSE(reachable_within(g, C, 0, 9));  // a destination outside the set
    CHECK_FALSE(reachable_within(g, C, 9, 9));  // a source outside the set, even from itself
}
