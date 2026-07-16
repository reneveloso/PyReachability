#include "reachability/dynamic/graph.hpp"

namespace reachability::dynamic {

const VertexSet DynamicGraph::kEmpty{};

void DynamicGraph::add_vertex(vertex_t v) {
    e_out_.try_emplace(v);
    e_in_.try_emplace(v);
}

void DynamicGraph::remove_vertex(vertex_t v) {
    e_out_.erase(v);
    e_in_.erase(v);
}

bool DynamicGraph::has_vertex(vertex_t v) const {
    return e_out_.find(v) != e_out_.end();
}

void DynamicGraph::add_edge(vertex_t u, vertex_t v) {
    e_out_[u].insert(v);
    e_in_[v].insert(u);
}

bool DynamicGraph::has_edge(vertex_t u, vertex_t v) const {
    auto it = e_out_.find(u);
    return it != e_out_.end() && it->second.count(v) > 0;
}

void DynamicGraph::remove_edge(vertex_t u, vertex_t v) {
    auto iu = e_out_.find(u);
    if (iu != e_out_.end()) iu->second.erase(v);
    auto iv = e_in_.find(v);
    if (iv != e_in_.end()) iv->second.erase(u);
}

const VertexSet& DynamicGraph::succ(vertex_t v) const {
    auto it = e_out_.find(v);
    return it == e_out_.end() ? kEmpty : it->second;
}

const VertexSet& DynamicGraph::pred(vertex_t v) const {
    auto it = e_in_.find(v);
    return it == e_in_.end() ? kEmpty : it->second;
}

void DynamicGraph::dag_add_vertex(vertex_t a) {
    dag_out_.try_emplace(a);
    dag_in_.try_emplace(a);
}

void DynamicGraph::dag_remove_vertex(vertex_t a) {
    dag_out_.erase(a);
    dag_in_.erase(a);
}

void DynamicGraph::dag_add_edge(vertex_t a, vertex_t b) {
    dag_out_[a].insert(b);
    dag_in_[b].insert(a);
}

void DynamicGraph::dag_remove_edge(vertex_t a, vertex_t b) {
    auto ia = dag_out_.find(a);
    if (ia != dag_out_.end()) ia->second.erase(b);
    auto ib = dag_in_.find(b);
    if (ib != dag_in_.end()) ib->second.erase(a);
}

const VertexSet& DynamicGraph::dag_succ(vertex_t a) const {
    auto it = dag_out_.find(a);
    return it == dag_out_.end() ? kEmpty : it->second;
}

const VertexSet& DynamicGraph::dag_pred(vertex_t a) const {
    auto it = dag_in_.find(a);
    return it == dag_in_.end() ? kEmpty : it->second;
}

} // namespace reachability::dynamic
