import numpy as np
import pytest
from pyreachability import Graph, catalog
from pyreachability.static import BFSDFS


def make_g():
    src = np.array([0, 1, 3], dtype=np.int32)
    dst = np.array([1, 2, 4], dtype=np.int32)
    return Graph.from_edges(src, dst, num_nodes=5)


def test_query():
    idx = BFSDFS(); idx.build(make_g())
    assert idx.query(0, 2) is True
    assert idx.query(2, 0) is False
    assert idx.query(2, 2) is True          # reflexive
    assert idx.index_size_bytes == 0


def test_query_batch():
    idx = BFSDFS(); idx.build(make_g())
    pairs = np.array([[0, 2], [2, 0], [3, 4]], dtype=np.int32)
    out = idx.query_batch(pairs)
    assert out.dtype == bool
    assert out.tolist() == [True, False, True]


def test_query_before_build_raises():
    with pytest.raises(RuntimeError):
        BFSDFS().query(0, 1)


def test_query_out_of_range_raises():
    idx = BFSDFS(); idx.build(make_g())
    with pytest.raises(IndexError):
        idx.query(0, 99)


def test_registered_in_catalog():
    assert "bfsdfs" in catalog.methods()
    assert catalog.get("bfsdfs") is BFSDFS
