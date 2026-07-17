import pytest

from pyreachability.dynamic import DynamicReachabilityIndex, UnsupportedOperation
from pyreachability.dynamic import base as dyn_base


class _InsertOnly(DynamicReachabilityIndex):
    """A stand-in for an insertion-only method (DBL is the real one)."""

    name = "_insert_only"
    supports = frozenset({dyn_base.EDGE_INSERT})

    def __init__(self):
        self.edges = []

    def build(self, graph):
        pass

    def insert_edge(self, u, v):
        self.edges.append((u, v))

    def query(self, u, v):
        return False

    def query_batch(self, pairs):
        raise NotImplementedError

    @property
    def index_size_bytes(self):
        return 0


def test_unsupported_operation_is_explicit():
    idx = _InsertOnly()
    with pytest.raises(UnsupportedOperation):
        idx.remove_edge(0, 1)
    with pytest.raises(UnsupportedOperation):
        idx.insert_vertex(0)
    with pytest.raises(UnsupportedOperation):
        idx.remove_vertex(0)


def test_capabilities_are_introspectable():
    # Consumers read `supports` and skip; they do not probe with try/except.
    assert dyn_base.EDGE_INSERT in _InsertOnly.supports
    assert dyn_base.EDGE_DELETE not in _InsertOnly.supports


def test_batch_insert_falls_back_to_a_loop():
    # Every dynamic index accepts batches; the capability says whether it has a
    # *better* algorithm than the loop, not whether batches are possible.
    idx = _InsertOnly()
    idx.insert_edges([(0, 1), (1, 2)])
    assert idx.edges == [(0, 1), (1, 2)]
    assert dyn_base.EDGE_INSERT_BATCH not in _InsertOnly.supports


def test_a_dynamic_index_is_a_reachability_index():
    from pyreachability import ReachabilityIndex
    assert issubclass(DynamicReachabilityIndex, ReachabilityIndex)


def test_default_supports_is_empty():
    # The base class declares no capabilities; a method that forgets to
    # override `supports` should not silently inherit someone else's.
    assert DynamicReachabilityIndex.supports == frozenset()


def test_cannot_instantiate_the_abc_directly():
    # DynamicReachabilityIndex inherits the abstract build/query/query_batch/
    # index_size_bytes contract from ReachabilityIndex; it must stay abstract.
    with pytest.raises(TypeError):
        DynamicReachabilityIndex()
