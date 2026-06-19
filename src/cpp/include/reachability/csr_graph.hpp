#pragma once
#include <cstdint>
#include <cstddef>
#include <vector>

namespace reachability {

using vid_t = std::int32_t;

class CSRGraph {
public:
    CSRGraph() = default;
    CSRGraph(vid_t n, const std::vector<vid_t>& src, const std::vector<vid_t>& dst);

    vid_t num_nodes() const { return n_; }
    std::size_t num_edges() const { return targets_.size(); }

    const vid_t* out_begin(vid_t u) const { return targets_.data() + offsets_[u]; }
    const vid_t* out_end(vid_t u) const { return targets_.data() + offsets_[u + 1]; }
    vid_t out_degree(vid_t u) const {
        return static_cast<vid_t>(offsets_[u + 1] - offsets_[u]);
    }

private:
    vid_t n_ = 0;
    std::vector<std::size_t> offsets_{0};   // size n_+1
    std::vector<vid_t> targets_;            // size m (deduped, no self-loops)
};

}  // namespace reachability
