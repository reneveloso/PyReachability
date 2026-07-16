import numpy as np
from hypothesis import given, settings, strategies as st
from pyreachability import Graph
from pyreachability.static import BFSDFS
from pyreachability._oracle import reachable_set, oracle_query


@st.composite
def digraphs(draw):
    n = draw(st.integers(min_value=1, max_value=12))
    max_e = n * n
    m = draw(st.integers(min_value=0, max_value=max_e))
    edges = draw(st.lists(
        st.tuples(st.integers(0, n - 1), st.integers(0, n - 1)),
        min_size=m, max_size=m))
    return n, edges


@settings(max_examples=200)
@given(digraphs())
def test_bfsdfs_matches_oracle(g):
    n, edges = g
    src = np.array([e[0] for e in edges], dtype=np.int32)
    dst = np.array([e[1] for e in edges], dtype=np.int32)
    graph = Graph.from_edges(src, dst, num_nodes=n)
    idx = BFSDFS(); idx.build(graph)
    reach = reachable_set(n, edges)
    for u in range(n):
        for v in range(n):
            assert idx.query(u, v) == oracle_query(reach, u, v)
