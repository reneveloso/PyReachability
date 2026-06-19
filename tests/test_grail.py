import numpy as np
import pytest
from hypothesis import given, settings, strategies as st
from pyreachability import Graph, GRAIL, catalog
from pyreachability._oracle import reachable_set, oracle_query


def test_basic_dag():
    g = Graph.from_edges(np.array([0, 0, 1, 2, 2], np.int32),
                         np.array([1, 2, 3, 3, 4], np.int32), num_nodes=5)
    idx = GRAIL(); idx.build(g)
    assert idx.query(0, 3) is True
    assert idx.query(3, 0) is False
    assert idx.query(4, 4) is True            # reflexive
    assert idx.index_size_bytes > 0


def test_cycle_via_scc():
    # 0->1->2->0 is one SCC; 2->3
    g = Graph.from_edges(np.array([0, 1, 2, 2], np.int32),
                         np.array([1, 2, 0, 3], np.int32), num_nodes=4)
    idx = GRAIL(); idx.build(g)
    assert idx.query(0, 2) is True            # same SCC
    assert idx.query(2, 0) is True            # same SCC
    assert idx.query(0, 3) is True
    assert idx.query(3, 0) is False


def test_errors_and_registration():
    with pytest.raises(RuntimeError):
        GRAIL().query(0, 1)
    g = Graph.from_edges(np.array([0], np.int32), np.array([1], np.int32), num_nodes=2)
    idx = GRAIL(); idx.build(g)
    with pytest.raises(IndexError):
        idx.query(0, 99)
    assert "grail" in catalog.methods()
    assert catalog.get("grail") is GRAIL


@st.composite
def digraphs(draw):
    n = draw(st.integers(1, 12))
    m = draw(st.integers(0, n * n))
    edges = draw(st.lists(st.tuples(st.integers(0, n - 1), st.integers(0, n - 1)),
                          min_size=m, max_size=m))
    return n, edges


def test_bidirectional_basic():
    g = Graph.from_edges(np.array([0, 0, 1, 2, 2], np.int32),
                         np.array([1, 2, 3, 3, 4], np.int32), num_nodes=5)
    idx = GRAIL(bidirectional=True); idx.build(g)
    assert idx.query(0, 3) is True
    assert idx.query(3, 0) is False
    assert idx.bidirectional is True


@settings(max_examples=200)
@given(digraphs(), st.booleans())
def test_grail_matches_oracle(g, bidirectional):
    n, edges = g
    src = np.array([e[0] for e in edges], dtype=np.int32)
    dst = np.array([e[1] for e in edges], dtype=np.int32)
    graph = Graph.from_edges(src, dst, num_nodes=n)
    idx = GRAIL(d=3, seed=12345, bidirectional=bidirectional); idx.build(graph)
    reach = reachable_set(n, edges)
    for u in range(n):
        for v in range(n):
            assert idx.query(u, v) == oracle_query(reach, u, v)
