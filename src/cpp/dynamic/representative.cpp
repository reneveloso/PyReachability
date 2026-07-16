#include "reachability/dynamic/representative.hpp"

#include <cassert>

namespace reachability::dynamic {

// ---- Representative (union-find) ----

void Representative::make_set(vertex_t v) {
    parent_[v] = v;
    rank_[v] = 0;
}

void Representative::erase(vertex_t v) {
    parent_.erase(v);
    rank_.erase(v);
}

bool Representative::contains(vertex_t v) const {
    return parent_.find(v) != parent_.end();
}

vertex_t Representative::find(vertex_t v) {
    assert(contains(v) && "Representative::find on unknown vertex");
    vertex_t root = v;
    while (parent_[root] != root) root = parent_[root];
    // path compression
    while (parent_[v] != root) {
        vertex_t next = parent_[v];
        parent_[v] = root;
        v = next;
    }
    return root;
}

vertex_t Representative::unite(const std::vector<vertex_t>& members, vertex_t chosen) {
    vertex_t root = find(chosen);
    for (vertex_t m : members) {
        vertex_t mroot = find(m);
        if (mroot == root) continue;
        parent_[mroot] = root;
        rank_[root] = rank_[root] > rank_[mroot] + 1 ? rank_[root] : rank_[mroot] + 1;
    }
    // `root` is now the root of the whole merged tree, but `chosen` may not
    // have been its own root at call time (root == find(chosen) could
    // differ from chosen). Re-point the tree so `chosen` is canonically the
    // representative: after this, find(chosen) == chosen unconditionally.
    if (root != chosen) {
        parent_[root] = chosen;
        rank_[chosen] = rank_[chosen] > rank_[root] + 1 ? rank_[chosen] : rank_[root] + 1;
        parent_[chosen] = chosen;
    }
    return chosen;
}

void Representative::repartition(const std::vector<std::vector<vertex_t>>& partitions) {
    // Reset every affected member first: a member of one partition may still be
    // pointed at by a member of another until all parents are cleared.
    for (const auto& part : partitions)
        for (vertex_t m : part) {
            parent_[m] = m;
            rank_[m] = 0;
        }
    for (const auto& part : partitions)
        if (!part.empty()) unite(part, part[0]);
}

} // namespace reachability::dynamic
