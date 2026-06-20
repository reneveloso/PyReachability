#include "reachability/tc.hpp"

namespace reachability {

void TC::build(const CSRGraph& dag) {
    n_ = dag.num_nodes();
    words_ = (std::size_t)(n_ + 63) / 64;
    bits_.assign((std::size_t)n_ * words_, 0ULL);

    // Topological order (Kahn); we then fill rows in reverse, so every successor's row is
    // complete before its predecessor's.
    std::vector<vid_t> indeg(n_, 0);
    for (vid_t u = 0; u < n_; ++u)
        for (const vid_t* it = dag.out_begin(u); it != dag.out_end(u); ++it)
            ++indeg[*it];
    std::vector<vid_t> order;
    order.reserve(n_);
    {
        std::vector<vid_t> ind = indeg, q;
        for (vid_t u = 0; u < n_; ++u) if (ind[u] == 0) q.push_back(u);
        std::size_t head = 0;
        while (head < q.size()) {
            vid_t u = q[head++];
            order.push_back(u);
            for (const vid_t* it = dag.out_begin(u); it != dag.out_end(u); ++it)
                if (--ind[*it] == 0) q.push_back(*it);
        }
    }

    // Fill in reverse topological order: row(u) = {u} | union of row(w) for successors w.
    for (std::size_t i = order.size(); i-- > 0;) {
        vid_t u = order[i];
        std::uint64_t* ru = &bits_[(std::size_t)u * words_];
        for (const vid_t* it = dag.out_begin(u); it != dag.out_end(u); ++it) {
            const std::uint64_t* rw = &bits_[(std::size_t)(*it) * words_];
            for (std::size_t k = 0; k < words_; ++k) ru[k] |= rw[k];
        }
        ru[(std::size_t)u >> 6] |= (1ULL << (u & 63));   // reflexive
    }
}

bool TC::query(vid_t u, vid_t v) const {
    return (bits_[(std::size_t)u * words_ + ((std::size_t)v >> 6)] >> (v & 63)) & 1ULL;
}

std::size_t TC::index_size_bytes() const {
    return bits_.size() * sizeof(std::uint64_t);
}

}  // namespace reachability
