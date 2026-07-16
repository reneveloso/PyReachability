import numpy as np
import pytest
from hypothesis import given, settings, strategies as st
from pyreachability import Graph, catalog
from pyreachability.static import HL
from pyreachability._oracle import reachable_set, oracle_query


def test_basic_dag():
    g = Graph.from_edges(np.array([0, 0, 1, 2, 2], np.int32),
                         np.array([1, 2, 3, 3, 4], np.int32), num_nodes=5)
    idx = HL(); idx.build(g)
    assert idx.query(0, 3) is True
    assert idx.query(3, 0) is False
    assert idx.query(4, 4) is True
    assert idx.index_size_bytes > 0


def test_cycle_via_scc():
    g = Graph.from_edges(np.array([0, 1, 2, 2], np.int32),
                         np.array([1, 2, 0, 3], np.int32), num_nodes=4)
    idx = HL(); idx.build(g)
    assert idx.query(0, 2) is True
    assert idx.query(2, 0) is True
    assert idx.query(0, 3) is True
    assert idx.query(3, 0) is False


def test_errors_and_registration():
    with pytest.raises(RuntimeError):
        HL().query(0, 1)
    g = Graph.from_edges(np.array([0], np.int32), np.array([1], np.int32), num_nodes=2)
    idx = HL(); idx.build(g)
    with pytest.raises(IndexError):
        idx.query(0, 99)
    assert "hl" in catalog.methods()
    assert catalog.get("hl") is HL


@st.composite
def digraphs(draw):
    n = draw(st.integers(1, 12))
    m = draw(st.integers(0, n * n))
    edges = draw(st.lists(st.tuples(st.integers(0, n - 1), st.integers(0, n - 1)),
                          min_size=m, max_size=m))
    return n, edges


@settings(max_examples=300)
@given(digraphs())
def test_hl_matches_oracle(g):
    n, edges = g
    src = np.array([e[0] for e in edges], dtype=np.int32)
    dst = np.array([e[1] for e in edges], dtype=np.int32)
    graph = Graph.from_edges(src, dst, num_nodes=n)
    idx = HL(); idx.build(graph)
    reach = reachable_set(n, edges)
    for u in range(n):
        for v in range(n):
            assert idx.query(u, v) == oracle_query(reach, u, v)


def test_two_hop_labels_introspection_dag():
    import numpy as np
    from pyreachability import Graph
    from pyreachability.static import HL
    # diamond DAG
    g = Graph.from_edges(np.array([0, 0, 1, 2], np.int32),
                         np.array([1, 2, 3, 3], np.int32), num_nodes=4)
    idx = HL(); idx.build(g)
    labels = idx.two_hop_labels()
    assert set(labels.keys()) == {0, 1, 2, 3}
    for v, lab in labels.items():
        assert set(lab.keys()) == {"Lin", "Lout"}
    # the labels must DECIDE reachability: Lout(u) intersects Lin(v) iff u reaches v
    def reaches(u, v):
        return bool(labels[u]["Lout"] & labels[v]["Lin"])
    assert reaches(0, 3) and reaches(1, 3) and not reaches(3, 0) and not reaches(1, 2)


def test_two_hop_labels_raises_on_cycle():
    import numpy as np
    import pytest
    from pyreachability import Graph
    from pyreachability.static import HL
    g = Graph.from_edges(np.array([0, 1], np.int32),
                         np.array([1, 0], np.int32), num_nodes=2)
    idx = HL(); idx.build(g)
    with pytest.raises(NotImplementedError):
        idx.two_hop_labels()
