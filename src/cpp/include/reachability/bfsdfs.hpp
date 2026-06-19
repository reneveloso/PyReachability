#pragma once
#include "reachability/csr_graph.hpp"

namespace reachability {
bool bfs_reaches(const CSRGraph& g, vid_t u, vid_t v);
}  // namespace reachability
