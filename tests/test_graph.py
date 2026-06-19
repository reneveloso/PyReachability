import numpy as np
import pytest
from pyreachability import Graph


def test_from_edges_basic():
    src = np.array([0, 0, 1, 2], dtype=np.int32)
    dst = np.array([1, 2, 2, 0], dtype=np.int32)
    g = Graph.from_edges(src, dst, num_nodes=3)
    assert g.num_nodes == 3
    assert g.num_edges == 4


def test_from_edges_single_array():
    edges = np.array([[0, 1], [1, 2], [2, 0]], dtype=np.int32)
    g = Graph.from_edges(edges, num_nodes=4)
    assert g.num_nodes == 4
    assert g.num_edges == 3


def test_from_edges_single_array_wrong_shape():
    with pytest.raises(ValueError):
        Graph.from_edges(np.array([0, 1, 2], dtype=np.int32), num_nodes=3)


def test_from_edges_requires_num_nodes():
    with pytest.raises(TypeError):
        Graph.from_edges(np.array([[0, 1]], dtype=np.int32))


def test_from_edges_length_mismatch():
    with pytest.raises(ValueError):
        Graph.from_edges(np.array([0, 1], np.int32),
                         np.array([1], np.int32), num_nodes=2)


def test_from_edges_out_of_range():
    with pytest.raises(IndexError):
        Graph.from_edges(np.array([0], np.int32),
                         np.array([5], np.int32), num_nodes=2)


def test_from_file_edgelist(tmp_path):
    p = tmp_path / "g.txt"
    p.write_text("# comment\n0 1\n1 2\n2 0\n")
    g = Graph.from_file(str(p), fmt="edgelist")
    assert g.num_nodes == 3
    assert g.num_edges == 3


def test_from_file_malformed_reports_line(tmp_path):
    p = tmp_path / "bad.txt"
    p.write_text("0 1\nNOTANUMBER\n")
    with pytest.raises(ValueError) as exc:
        Graph.from_file(str(p), fmt="edgelist")
    assert "line 2" in str(exc.value)
