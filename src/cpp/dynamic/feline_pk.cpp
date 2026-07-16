#include "reachability/dynamic/feline_pk.hpp"

#include "reachability/dynamic/query.hpp"

namespace reachability::dynamic {

void FelinePK::insert_vertex(vertex_t v) {
    // Alg. 7: add to V, r(v) = v, append end of X / front of Y.
    g_.add_vertex(v);
    g_.dag_add_vertex(v);
    r_.make_set(v);
    idx_.append_isolated(v);
}

void FelinePK::remove_vertex(vertex_t v) {
    // Alg. 8: reverse of Alg. 7 (v must be isolated in E and its own representative).
    idx_.remove(v);
    r_.erase(v);
    g_.dag_remove_vertex(v);
    g_.remove_vertex(v);
}

bool FelinePK::reachable(vertex_t u, vertex_t v) {
    if (!r_.contains(u) || !r_.contains(v)) return false;
    vertex_t a = r_.find(u), b = r_.find(v);
    if (a == b) return true; // same SCC
    return dyn_reachable(g_, idx_, a, b);
}

std::size_t FelinePK::index_size_bytes() const {
    // Estimate only — no exact accounting of unordered_map's internal per-node
    // overhead. The reference implementation has no equivalent method (it was a
    // research tool, not a benchmarked catalog entry); this exists because
    // ReachabilityIndex requires the property and the benchmark harness reads it.
    return idx_.size_bytes() + r_.size_bytes();
}

} // namespace reachability::dynamic
