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
