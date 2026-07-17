#include "doctest.h"
#include "reachability/dynamic/index.hpp"

using reachability::dynamic::DynIndex;
using reachability::dynamic::DynamicGraph;
using reachability::dynamic::build_suborder;

TEST_CASE("DynIndex: append_isolated lands at the bottom-right corner") {
    DynIndex idx;
    idx.append_isolated(0);
    idx.append_isolated(1);
    CHECK(idx.has(0));
    CHECK(idx.size() == 2);
    // Alg. 7: end of X, front of Y. So a later vertex has greater X and smaller Y.
    CHECK(idx.x(0) < idx.x(1));
    CHECK(idx.y(0) > idx.y(1));
}

TEST_CASE("DynIndex: remove leaves a gap and does not disturb the rest") {
    DynIndex idx;
    for (unsigned v = 0; v < 3; ++v) idx.append_isolated(v);
    const auto x0 = idx.x(0), x2 = idx.x(2);
    idx.remove(1);
    CHECK_FALSE(idx.has(1));
    CHECK(idx.x(0) == x0);      // survivors keep their coordinates: no compaction
    CHECK(idx.x(2) == x2);
    CHECK(idx.size() == 2);
}

TEST_CASE("build_suborder: ranks only the induced sub-DAG") {
    DynamicGraph g;
    for (unsigned v = 0; v < 3; ++v) g.dag_add_vertex(v);
    g.dag_add_edge(0, 1);
    g.dag_add_edge(1, 2);
    // Restrict to {0, 2}: the 0->1->2 path is NOT an edge inside the set, so the
    // sub-DAG has no edges and both orders are valid; ranks are positional by `reps`.
    auto ord = build_suborder(g, {0, 2});
    CHECK(ord.x_rank.size() == 2);
    CHECK(ord.y_rank.size() == 2);
}

TEST_CASE("build_suborder: an edge inside the set constrains the order") {
    // The case above only exercises the filter's *rejection* path: with {0,2} the
    // sub-DAG comes out edgeless. This one exercises the *acceptance* path — 0->1 is
    // internal to `reps` and must be respected on both axes. Nothing covered that.
    DynamicGraph g;
    for (unsigned v = 0; v < 3; ++v) g.dag_add_vertex(v);
    g.dag_add_edge(0, 1);
    auto ord = build_suborder(g, {0, 1});   // ranks are positional by `reps`
    CHECK(ord.x_rank[0] < ord.x_rank[1]);
    CHECK(ord.y_rank[0] < ord.y_rank[1]);
}
