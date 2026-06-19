import numpy as np
import pytest
from pyreachability import ReachabilityIndex, catalog


def test_register_and_lookup():
    @catalog.register
    class Dummy(ReachabilityIndex):
        name = "dummy"
        def build(self, graph): self._n = graph.num_nodes
        def query(self, u, v): return u == v
        def query_batch(self, pairs):
            p = np.asarray(pairs)
            return np.array([self.query(int(a), int(b)) for a, b in p], dtype=bool)
        @property
        def index_size_bytes(self): return 0

    assert "dummy" in catalog.methods()
    assert catalog.methods() == sorted(catalog.methods())
    cls = catalog.get("dummy")
    assert cls is Dummy


def test_get_unknown_raises():
    with pytest.raises(KeyError):
        catalog.get("does-not-exist")


def test_cannot_instantiate_abstract():
    with pytest.raises(TypeError):
        ReachabilityIndex()
