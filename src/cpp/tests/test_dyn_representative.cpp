#include "doctest.h"
#include "reachability/dynamic/representative.hpp"

using reachability::dynamic::Representative;

TEST_CASE("Representative: singletons are their own root") {
    Representative r;
    r.make_set(0); r.make_set(1);
    CHECK(r.contains(0));
    CHECK(r.find(0) == 0);
    CHECK(r.find(1) == 1);
    CHECK_FALSE(r.contains(2));
}

TEST_CASE("Representative: unite makes `chosen` the root unconditionally") {
    Representative r;
    for (unsigned v = 0; v < 4; ++v) r.make_set(v);
    // Pick a `chosen` that is NOT already a root of the merged set.
    r.unite({0, 1}, 1);          // 1 is now the root of {0,1}
    const auto root = r.unite({0, 1, 2, 3}, 3);
    CHECK(root == 3);
    for (unsigned v = 0; v < 4; ++v) CHECK(r.find(v) == 3);
}

TEST_CASE("Representative: erase removes a singleton") {
    Representative r;
    r.make_set(7);
    r.erase(7);
    CHECK_FALSE(r.contains(7));
}

TEST_CASE("Representative: unite re-points when `chosen` is not the current root") {
    Representative r;
    for (unsigned v = 0; v < 3; ++v) r.make_set(v);
    r.unite({0, 1}, 1);          // 1 becomes the root of {0,1}
    REQUIRE(r.find(0) == 1);     // precondition: 0's root is 1, NOT 0
    // Now unite with chosen = 0, which is NOT its own root at call time. This is the
    // branch fold_cycle depends on: the postcondition must hold anyway.
    const auto root = r.unite({0, 2}, 0);
    CHECK(root == 0);
    CHECK(r.find(0) == 0);
    CHECK(r.find(1) == 0);       // the old root now resolves to `chosen`
    CHECK(r.find(2) == 0);
}

TEST_CASE("Representative: repartition splits a component and leaves no stale state") {
    // Ported from the reference's own test (test/test_dynamic.cpp:438-451), which Task 1
    // omitted. split_component depends on this contract: it re-elects representatives among
    // a folded component's members, so a repartition that left stale parent/rank behind
    // would surface as a randomised-stress failure, far from its cause.
    Representative r;
    for (unsigned v = 0; v < 5; ++v) r.make_set(v);
    r.unite({0, 1, 2, 3, 4}, 2);            // one component, representative 2
    REQUIRE(r.find(0) == 2);
    REQUIRE(r.find(4) == 2);

    r.repartition({{0, 1}, {2, 3, 4}});     // split into two components
    CHECK(r.find(0) == 0);                  // a partition's rep is its first member
    CHECK(r.find(1) == 0);
    CHECK(r.find(2) == 2);
    CHECK(r.find(3) == 2);
    CHECK(r.find(4) == 2);
    CHECK(r.find(0) != r.find(2));          // the partitions are distinct components

    // Splitting again, into singletons, must work: no stale parent/rank state.
    r.repartition({{0}, {1}, {2}, {3}, {4}});
    for (unsigned v = 0; v < 5; ++v) CHECK(r.find(v) == v);
}
