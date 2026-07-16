#include "doctest.h"
#include "reachability/dynamic/xy_ordering.hpp"
#include <vector>

using reachability::dynamic::compute_xy_ordering;

TEST_CASE("compute_xy_ordering: both axes are valid topological orders") {
    // 0 -> 1 -> 3, 0 -> 2 -> 3
    std::vector<std::vector<uint32_t>> adj = {{1, 2}, {3}, {3}, {}};
    auto ord = compute_xy_ordering(4, [&](uint32_t u, const auto& emit) {
        for (uint32_t w : adj[u]) emit(w);
    });
    for (uint32_t u = 0; u < 4; ++u)
        for (uint32_t w : adj[u]) {
            CHECK(ord.x_rank[u] < ord.x_rank[w]);
            CHECK(ord.y_rank[u] < ord.y_rank[w]);
        }
}

TEST_CASE("compute_xy_ordering: isolated vertices are kept") {
    // vertex 1 is isolated; it must still get a rank, not be dropped.
    std::vector<std::vector<uint32_t>> adj = {{2}, {}, {}};
    auto ord = compute_xy_ordering(3, [&](uint32_t u, const auto& emit) {
        for (uint32_t w : adj[u]) emit(w);
    });
    CHECK(ord.x_rank.size() == 3);
    CHECK(ord.y_rank.size() == 3);
    CHECK(ord.x_rank[0] < ord.x_rank[2]);
}

TEST_CASE("compute_xy_ordering: a cycle is reported, not silently mis-ordered") {
    // 0 -> 1 -> 0. In the dynamic path this can only mean the E_DAG invariant is
    // broken (fold/split bug), so it must throw rather than return a bogus order.
    std::vector<std::vector<uint32_t>> adj = {{1}, {0}};
    CHECK_THROWS_AS(compute_xy_ordering(2, [&](uint32_t u, const auto& emit) {
        for (uint32_t w : adj[u]) emit(w);
    }), std::runtime_error);
}
