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
