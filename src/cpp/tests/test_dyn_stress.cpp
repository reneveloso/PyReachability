#include "doctest.h"
#include "reachability/dynamic/feline_pk.hpp"

#include <cstdint>
#include <queue>
#include <random>
#include <string>
#include <unordered_set>

using reachability::dynamic::DynIndex;
using reachability::dynamic::DynamicGraph;
using reachability::dynamic::FelinePK;
using reachability::dynamic::vertex_t;

// Ground truth: BFS over the digraph E, independent of the index. Ported from the
// reference's test/oracle.hpp.
static bool bfs_reachable(const DynamicGraph& g, vertex_t u, vertex_t v) {
    if (u == v) return true;
    std::unordered_set<vertex_t> visited;
    std::queue<vertex_t> q;
    visited.insert(u);
    q.push(u);
    while (!q.empty()) {
        vertex_t cur = q.front();
        q.pop();
        for (vertex_t w : g.succ(cur)) {
            if (w == v) return true;
            if (visited.insert(w).second) q.push(w);
        }
    }
    return false;
}

// The index invariant the dominance cut rests on: every E_DAG edge must be increasing in
// both coordinates. A reachability oracle alone can miss a corrupted index — the negative
// cut is conservative, so a violated invariant can stay silent on small graphs and only
// produce wrong answers later. Ported from the reference's test_dynamic.cpp.
static bool dag_invariant_holds(const FelinePK& pk, std::string& why) {
    const DynIndex& idx = pk.index();
    for (const auto& kv : pk.graph().dag_out_all()) {
        vertex_t p = kv.first;
        for (vertex_t q : kv.second) {
            if (!(idx.x(p) < idx.x(q)) || !(idx.y(p) < idx.y(q))) {
                why = "E_DAG edge (" + std::to_string(p) + "," + std::to_string(q) +
                      ") violates the index invariant";
                return false;
            }
        }
    }
    return true;
}

// Random interleaving of insertions AND removals. After EVERY operation: the index
// invariant must hold, and all pairs must agree with brute force over an independently
// maintained oracle digraph. Fixed seed for reproducibility.
TEST_CASE("FelinePK: random insert/remove sequences agree with the oracle") {
    std::mt19937 rng(13579246u);
    for (int trial = 0; trial < 200; ++trial) {
        std::uniform_int_distribution<uint32_t> ndist(4, 9);
        const vertex_t N = static_cast<vertex_t>(ndist(rng));

        FelinePK pk;
        DynamicGraph oracle;
        for (vertex_t v = 0; v < N; ++v) {
            pk.insert_vertex(v);
            oracle.add_vertex(v);
        }

        std::uniform_int_distribution<uint32_t> pick(0, N - 1);
        std::uniform_int_distribution<int> coin(0, 99);

        for (int step = 0; step < 40; ++step) {
            const vertex_t a = static_cast<vertex_t>(pick(rng));
            const vertex_t b = static_cast<vertex_t>(pick(rng));
            if (a == b) continue;  // self-loops never change reachability

            if (coin(rng) < 60) {  // 60% insert, 40% remove
                pk.insert_edge(a, b);
                oracle.add_edge(a, b);
            } else {
                pk.remove_edge(a, b);
                oracle.remove_edge(a, b);
            }

            std::string why;
            REQUIRE_MESSAGE(dag_invariant_holds(pk, why),
                            "trial=" << trial << " step=" << step << " N=" << N << ": " << why);

            for (vertex_t s = 0; s < N; ++s)
                for (vertex_t t = 0; t < N; ++t)
                    REQUIRE_MESSAGE(pk.reachable(s, t) == bfs_reachable(oracle, s, t),
                                    "trial=" << trial << " step=" << step << " N=" << N
                                             << " " << s << "->" << t);
        }
    }
}
