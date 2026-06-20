import numpy as np
import pytest
from hypothesis import given, settings, strategies as st
from pyreachability import Graph, TC, TreeCover, catalog
from pyreachability._oracle import reachable_set, oracle_query

METHODS = [TC, TreeCover]


@pytest.mark.parametrize("Method", METHODS)
def test_basic_dag(Method):
    g = Graph.from_edges(np.array([0, 0, 1, 2, 2], np.int32),
                         np.array([1, 2, 3, 3, 4], np.int32), num_nodes=5)
    idx = Method(); idx.build(g)
    assert idx.query(0, 3) is True
    assert idx.query(3, 0) is False
    assert idx.query(4, 4) is True
    assert idx.index_size_bytes > 0


@pytest.mark.parametrize("Method", METHODS)
def test_cycle_via_scc(Method):
    g = Graph.from_edges(np.array([0, 1, 2, 2], np.int32),
                         np.array([1, 2, 0, 3], np.int32), num_nodes=4)
    idx = Method(); idx.build(g)
    assert idx.query(0, 2) is True
    assert idx.query(2, 0) is True
    assert idx.query(0, 3) is True
    assert idx.query(3, 0) is False


@pytest.mark.parametrize("Method,name", [(TC, "tc"), (TreeCover, "treecover")])
def test_errors_and_registration(Method, name):
    with pytest.raises(RuntimeError):
        Method().query(0, 1)
    g = Graph.from_edges(np.array([0], np.int32), np.array([1], np.int32), num_nodes=2)
    idx = Method(); idx.build(g)
    with pytest.raises(IndexError):
        idx.query(0, 99)
    assert name in catalog.methods()
    assert catalog.get(name) is Method


@st.composite
def digraphs(draw):
    n = draw(st.integers(1, 12))
    m = draw(st.integers(0, n * n))
    edges = draw(st.lists(st.tuples(st.integers(0, n - 1), st.integers(0, n - 1)),
                          min_size=m, max_size=m))
    return n, edges


@settings(max_examples=150)
@given(digraphs(), st.sampled_from(METHODS))
def test_matches_oracle(g, Method):
    n, edges = g
    src = np.array([e[0] for e in edges], dtype=np.int32)
    dst = np.array([e[1] for e in edges], dtype=np.int32)
    graph = Graph.from_edges(src, dst, num_nodes=n)
    idx = Method(); idx.build(graph)
    reach = reachable_set(n, edges)
    for u in range(n):
        for v in range(n):
            assert idx.query(u, v) == oracle_query(reach, u, v)
