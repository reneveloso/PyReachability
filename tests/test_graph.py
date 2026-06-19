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


def test_to_edges_roundtrip():
    src = np.array([0, 0, 1, 2], np.int32)
    dst = np.array([2, 1, 2, 0], np.int32)
    g = Graph.from_edges(src, dst, num_nodes=3)
    s2, d2 = g.to_edges()
    assert s2.dtype == np.int32 and d2.dtype == np.int32
    assert len(s2) == g.num_edges
    assert set(zip(s2.tolist(), d2.tolist())) == {(0, 2), (0, 1), (1, 2), (2, 0)}
    # round-trips: rebuilding yields the same edge count
    g2 = Graph.from_edges(s2, d2, num_nodes=3)
    assert g2.num_edges == g.num_edges


def test_from_file_gra(tmp_path):
    # GRAIL/GREACH .gra format: header line, vertex count, then "id: succ... #"
    p = tmp_path / "g.gra"
    p.write_text("graph_for_greach\n4\n0: 1 2 #\n1: 3 #\n2: 3 #\n3: #\n")
    g = Graph.from_file(str(p), fmt="gra")
    assert g.num_nodes == 4          # declared count (node 3 is isolated as a sink)
    assert g.num_edges == 4


def test_from_file_gra_no_header(tmp_path):
    # Older .gra variant: vertex count on the first line, no header marker.
    p = tmp_path / "g2.gra"
    p.write_text("3\n0: 1 #\n1: 2 #\n2: #\n")
    g = Graph.from_file(str(p), fmt="gra")
    assert g.num_nodes == 3
    assert g.num_edges == 2


def test_from_file_gra_gzip(tmp_path):
    import gzip
    p = tmp_path / "g.gra.gz"
    with gzip.open(p, "wt") as fh:
        fh.write("graph_for_greach\n3\n0: 1 2 #\n1: #\n2: #\n")
    g = Graph.from_file(str(p), fmt="gra")   # gzip detected by .gz extension
    assert g.num_nodes == 3
    assert g.num_edges == 2


def test_from_file_unknown_fmt(tmp_path):
    p = tmp_path / "x.txt"
    p.write_text("0 1\n")
    with pytest.raises(ValueError):
        Graph.from_file(str(p), fmt="nope")


def test_from_file_malformed_reports_line(tmp_path):
    p = tmp_path / "bad.txt"
    p.write_text("0 1\nNOTANUMBER\n")
    with pytest.raises(ValueError) as exc:
        Graph.from_file(str(p), fmt="edgelist")
    assert "line 2" in str(exc.value)
