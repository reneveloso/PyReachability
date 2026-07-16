#include "doctest.h"
#include "reachability/dynamic/graph.hpp"

using reachability::dynamic::DynamicGraph;
using reachability::dynamic::vertex_t;

TEST_CASE("DynamicGraph: edges land in both directions") {
    DynamicGraph g;
    g.add_vertex(0); g.add_vertex(1);
    g.add_edge(0, 1);
    CHECK(g.succ(0).count(1) == 1);
    CHECK(g.pred(1).count(0) == 1);
}

TEST_CASE("DynamicGraph: remove_edge is idempotent and total") {
    DynamicGraph g;
    g.add_vertex(0); g.add_vertex(1);
    g.add_edge(0, 1);
    g.remove_edge(0, 1);
    CHECK(g.succ(0).count(1) == 0);
    g.remove_edge(0, 1);   // idempotent: removing an absent edge is a no-op
    g.remove_edge(7, 8);   // unknown vertices must not crash
    CHECK(g.succ(0).empty());
}

TEST_CASE("DynamicGraph: E_DAG is independent of E") {
    DynamicGraph g;
    g.dag_add_vertex(0); g.dag_add_vertex(1);
    g.dag_add_edge(0, 1);
    CHECK(g.dag_succ(0).count(1) == 1);
    g.dag_remove_edge(0, 1);
    CHECK(g.dag_succ(0).empty());
}

TEST_CASE("DynamicGraph: E adjacency and DAG adjacency, ported from reference test_dynamic_graph_edges") {
    DynamicGraph g;
    for (vertex_t v = 0; v < 4; ++v) g.add_vertex(v);
    g.add_edge(0, 1);
    g.add_edge(0, 2);
    g.add_edge(1, 3);
    CHECK(g.succ(0).count(1));
    CHECK(g.succ(0).count(2));
    CHECK(g.succ(0).size() == 2);
    CHECK(g.pred(3).count(1));
    CHECK(g.pred(3).size() == 1);
    CHECK(g.succ(3).empty());

    g.dag_add_vertex(0); g.dag_add_vertex(1);
    g.dag_add_edge(0, 1);
    CHECK(g.dag_succ(0).count(1));
    CHECK(g.dag_pred(1).count(0));
    g.dag_remove_edge(0, 1);
    CHECK(g.dag_succ(0).empty());
    CHECK(g.dag_pred(1).empty());
}

TEST_CASE("DynamicGraph: remove_edge, ported from reference test_dynamic_graph_remove_edge") {
    DynamicGraph g;
    for (vertex_t v = 0; v < 3; ++v) g.add_vertex(v);
    g.add_edge(0, 1);
    g.add_edge(0, 2);
    CHECK(g.has_edge(0, 1));
    CHECK(g.has_edge(0, 2));
    CHECK_FALSE(g.has_edge(1, 0));
    CHECK_FALSE(g.has_edge(7, 8));   // unknown vertices -> no edge

    g.remove_edge(0, 1);
    CHECK_FALSE(g.has_edge(0, 1));
    CHECK_FALSE(g.succ(0).count(1));
    CHECK_FALSE(g.pred(1).count(0));
    CHECK(g.has_edge(0, 2));   // other edge intact

    g.remove_edge(0, 1);   // idempotent
    g.remove_edge(7, 8);   // unknown vertices: must not crash
    CHECK(g.has_edge(0, 2));
    CHECK(g.out_all().size() == 3);   // out_all exposes every vertex
}

TEST_CASE("DynamicGraph: has_vertex and remove_vertex") {
    DynamicGraph g;
    CHECK_FALSE(g.has_vertex(0));
    g.add_vertex(0);
    CHECK(g.has_vertex(0));
    g.remove_vertex(0);
    CHECK_FALSE(g.has_vertex(0));
    CHECK(g.succ(0).empty());
    CHECK(g.pred(0).empty());
}

TEST_CASE("DynamicGraph: dag_remove_vertex drops the vertex once isolated") {
    DynamicGraph g;
    g.dag_add_vertex(0); g.dag_add_vertex(1);
    g.dag_add_edge(0, 1);
    g.dag_remove_edge(0, 1);   // remove_vertex requires the vertex to be isolated first
    g.dag_remove_vertex(1);
    CHECK(g.dag_succ(0).empty());
    CHECK_FALSE(g.dag_out_all().count(1));
}
