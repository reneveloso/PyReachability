#include "doctest.h"
#include "reachability/bfsdfs.hpp"
#include "reachability/csr_graph.hpp"
#include <vector>
using namespace reachability;

TEST_CASE("bfs reachability") {
    std::vector<vid_t> src{0, 1, 3};
    std::vector<vid_t> dst{1, 2, 4};
    CSRGraph g(5, src, dst);
    CHECK(bfs_reaches(g, 0, 2) == true);
    CHECK(bfs_reaches(g, 2, 0) == false);
    CHECK(bfs_reaches(g, 0, 4) == false);
    CHECK(bfs_reaches(g, 3, 4) == true);
    CHECK(bfs_reaches(g, 2, 2) == true);   // reflexive
}
