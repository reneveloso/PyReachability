#include "doctest.h"
#include "reachability/dynamic/feline_pk.hpp"

using reachability::dynamic::FelinePK;

TEST_CASE("FelinePK: an isolated vertex reaches only itself") {
    FelinePK pk;
    pk.insert_vertex(0);
    pk.insert_vertex(1);
    CHECK(pk.reachable(0, 0));      // reflexive
    CHECK_FALSE(pk.reachable(0, 1));
    CHECK_FALSE(pk.reachable(1, 0));
}

TEST_CASE("FelinePK: remove_vertex drops it from graph and index") {
    FelinePK pk;
    pk.insert_vertex(0);
    pk.insert_vertex(1);
    pk.remove_vertex(1);
    // Alg. 8 must reach all three structures, not just the digraph. Dropping the
    // idx_.remove(v) or r_.erase(v) call — or passing the wrong vertex to either —
    // leaves a live coordinate or a stale set behind, which the graph check alone
    // cannot see.
    CHECK_FALSE(pk.graph().has_vertex(1));
    CHECK_FALSE(pk.index().has(1));
    CHECK_FALSE(pk.rep().contains(1));
    CHECK(pk.reachable(0, 0));
}

TEST_CASE("FelinePK: insert_edge makes the target reachable") {
    FelinePK pk;
    for (unsigned v = 0; v < 3; ++v) pk.insert_vertex(v);
    pk.insert_edge(0, 1);
    pk.insert_edge(1, 2);
    CHECK(pk.reachable(0, 2));
    CHECK_FALSE(pk.reachable(2, 0));
}

TEST_CASE("FelinePK: closing a cycle folds it into one component") {
    FelinePK pk;
    for (unsigned v = 0; v < 3; ++v) pk.insert_vertex(v);
    pk.insert_edge(0, 1);
    pk.insert_edge(1, 2);
    pk.insert_edge(2, 0);           // closes the cycle: {0,1,2} is now one SCC
    CHECK(pk.rep().find(0) == pk.rep().find(1));
    CHECK(pk.rep().find(1) == pk.rep().find(2));

    // No all-pairs loop here: reachable() short-circuits on `a == b` once the
    // representatives coincide, which the two CHECKs above already established. Such a
    // loop would pass over a completely corrupted index — it asserts nothing.
    //
    // What the fold must ALSO do is collapse the three DAG nodes into one. Check the DAG
    // vertex SET, not the edges: fold_cycle strips every edge touching a folded rep before
    // it removes the vertices, so an assertion on dag_succ() being empty holds either way
    // and proves nothing. Membership is what dag_remove_vertex actually changes.
    const auto r = pk.rep().find(0);
    CHECK(pk.graph().dag_out_all().count(r) == 1);    // the representative survives
    for (unsigned v = 0; v < 3; ++v)
        if (v != r) CHECK(pk.graph().dag_out_all().count(v) == 0);   // members left E_DAG
    CHECK(pk.graph().dag_succ(r).count(r) == 0);      // no self-loop was rewired in
}

TEST_CASE("FelinePK: a fold keeps outside reachability intact") {
    FelinePK pk;
    for (unsigned v = 0; v < 5; ++v) pk.insert_vertex(v);
    pk.insert_edge(3, 0);           // 3 feeds the cycle
    pk.insert_edge(0, 1);
    pk.insert_edge(1, 2);
    pk.insert_edge(2, 0);           // fold {0,1,2}
    pk.insert_edge(2, 4);           // the cycle feeds 4
    CHECK(pk.reachable(3, 4));      // through the folded component
    CHECK(pk.reachable(3, 1));
    CHECK_FALSE(pk.reachable(4, 3));
}

TEST_CASE("FelinePK: removing the only link between components cuts reachability") {
    FelinePK pk;
    for (unsigned v = 0; v < 3; ++v) pk.insert_vertex(v);
    pk.insert_edge(0, 1);
    pk.insert_edge(1, 2);
    const int64_t x0 = pk.index().x(0), y0 = pk.index().y(0);
    const int64_t x1 = pk.index().x(1), y1 = pk.index().y(1);
    const int64_t x2 = pk.index().x(2), y2 = pk.index().y(2);
    CHECK(pk.reachable(0, 2));

    pk.remove_edge(1, 2);
    CHECK_FALSE(pk.reachable(0, 2));
    CHECK_FALSE(pk.reachable(1, 2));
    CHECK(pk.reachable(0, 1));

    // Removing an edge never invalidates a topological order: nothing moves.
    CHECK((pk.index().x(0) == x0 && pk.index().y(0) == y0));
    CHECK((pk.index().x(1) == x1 && pk.index().y(1) == y1));
    CHECK((pk.index().x(2) == x2 && pk.index().y(2) == y2));
}

TEST_CASE("FelinePK: a parallel edge keeps the DAG edge alive") {
    // Two distinct E edges between the same pair of components: removing one must NOT
    // remove the E_DAG edge. Removing the second one must.
    FelinePK pk;
    for (unsigned v = 0; v < 4; ++v) pk.insert_vertex(v);
    pk.insert_edge(0, 1); pk.insert_edge(1, 0);   // component {0,1}
    pk.insert_edge(2, 3); pk.insert_edge(3, 2);   // component {2,3}
    pk.insert_edge(0, 2);                         // first link between the components
    pk.insert_edge(1, 3);                         // second link between the SAME components
    CHECK(pk.reachable(0, 3));

    pk.remove_edge(0, 2);
    CHECK(pk.reachable(0, 3));      // still linked through the parallel edge (1,3)
    pk.remove_edge(1, 3);
    CHECK_FALSE(pk.reachable(0, 3)); // unreachable once both links are gone
    CHECK(pk.reachable(0, 1));       // the components themselves are intact
    CHECK(pk.reachable(2, 3));
}

TEST_CASE("FelinePK: removing an edge inside a component splits it") {
    FelinePK pk;
    for (unsigned v = 0; v < 3; ++v) pk.insert_vertex(v);
    pk.insert_edge(0, 1);
    pk.insert_edge(1, 2);
    pk.insert_edge(2, 0);           // fold {0,1,2}
    CHECK(pk.rep().find(0) == pk.rep().find(2));
    for (unsigned v = 0; v < 3; ++v)
        CHECK(pk.index().has(v));   // folded members keep their coordinates

    pk.remove_edge(2, 0);           // the cycle breaks: back to a 0 -> 1 -> 2 chain
    CHECK(pk.rep().find(0) != pk.rep().find(2));
    CHECK(pk.reachable(0, 1));
    CHECK(pk.reachable(1, 2));
    CHECK(pk.reachable(0, 2));
    CHECK_FALSE(pk.reachable(2, 0));
    CHECK_FALSE(pk.reachable(1, 0));
    CHECK_FALSE(pk.reachable(2, 1));
    for (unsigned v = 0; v < 3; ++v)
        CHECK(pk.index().has(v));   // every re-elected representative has a coordinate
}

TEST_CASE("FelinePK: an internal edge whose removal does not split the component") {
    FelinePK pk;
    for (unsigned v = 0; v < 3; ++v) pk.insert_vertex(v);
    pk.insert_edge(0, 1);
    pk.insert_edge(1, 2);
    pk.insert_edge(2, 0);
    pk.insert_edge(1, 0);           // redundant back edge inside the SCC

    pk.remove_edge(1, 0);           // still strongly connected through 1->2->0
    CHECK(pk.reachable(1, 0));
    CHECK(pk.reachable(0, 1));
    CHECK(pk.reachable(2, 1));
    CHECK(pk.reachable(0, 2));
}

TEST_CASE("FelinePK: a split keeps the component's external boundary intact") {
    // 0 -> 1 (external predecessor into the component)
    // SCC {1,2,3}: 1->2, 2->3, 3->1
    // 3 -> 4 (external successor out of the component)
    FelinePK pk;
    for (unsigned v = 0; v < 5; ++v) pk.insert_vertex(v);
    pk.insert_edge(0, 1);
    pk.insert_edge(1, 2); pk.insert_edge(2, 3); pk.insert_edge(3, 1);
    pk.insert_edge(3, 4);
    CHECK(pk.reachable(0, 4));
    CHECK(pk.reachable(3, 1));
    CHECK(pk.reachable(1, 3));

    pk.remove_edge(3, 1);           // breaks the cycle -> chain 1->2->3

    // The chain survives.
    CHECK(pk.reachable(1, 2));
    CHECK(pk.reachable(2, 3));
    CHECK(pk.reachable(1, 3));

    // The cycle is gone.
    CHECK_FALSE(pk.reachable(3, 1));
    CHECK_FALSE(pk.reachable(2, 1));
    CHECK_FALSE(pk.reachable(3, 2));

    // The inbound boundary still works (pins split_component's pred(w) reinsertion loop).
    CHECK(pk.reachable(0, 1));
    CHECK(pk.reachable(0, 2));
    CHECK(pk.reachable(0, 3));
    CHECK(pk.reachable(0, 4));

    // The outbound boundary still works (pins its succ(w) reinsertion loop).
    CHECK(pk.reachable(1, 4));
    CHECK(pk.reachable(2, 4));
    CHECK(pk.reachable(3, 4));

    // Nothing spurious appeared.
    CHECK_FALSE(pk.reachable(4, 0));
    CHECK_FALSE(pk.reachable(4, 3));
    CHECK_FALSE(pk.reachable(1, 0));
}

TEST_CASE("FelinePK: remove_edge no-ops on absent edges and unknown vertices") {
    FelinePK pk;
    pk.insert_vertex(0);
    pk.insert_vertex(1);
    pk.insert_edge(0, 1);

    pk.remove_edge(1, 0);           // this edge never existed
    CHECK(pk.reachable(0, 1));
    pk.remove_edge(5, 6);           // unknown vertices must not crash
    CHECK(pk.reachable(0, 1));

    pk.insert_edge(0, 0);           // self-loop
    pk.remove_edge(0, 0);           // must be a clean no-op
    CHECK(pk.reachable(0, 0));
    CHECK(pk.reachable(0, 1));      // the real edge was left alone

    pk.remove_edge(0, 1);           // the real removal still works afterwards
    CHECK_FALSE(pk.reachable(0, 1));
}
