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
    CHECK_FALSE(pk.graph().has_vertex(1));
    CHECK(pk.reachable(0, 0));
}
