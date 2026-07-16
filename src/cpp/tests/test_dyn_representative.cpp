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
