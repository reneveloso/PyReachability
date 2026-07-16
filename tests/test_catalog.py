import numpy as np
import pytest
from pyreachability import ReachabilityIndex, catalog
from pyreachability.dynamic.base import DynamicReachabilityIndex


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


def test_methods_can_be_filtered_by_kind():
    # No dynamic method is registered in the library yet (Task 13 lands the
    # first one), so without a stand-in the partition assertions below would
    # pass by vacuity: sorted(static + []) == sorted(all) holds no matter how
    # "dynamic" is computed, and an empty set is disjoint from anything.
    # Registering a fake dynamic class here — same convention as `Dummy` in
    # test_register_and_lookup and `_InsertOnly` in test_dynamic_base.py —
    # makes the dynamic branch actually get exercised.
    @catalog.register
    class _DummyDynamic(DynamicReachabilityIndex):
        name = "_dummy_dynamic"
        def build(self, graph): pass
        def query(self, u, v): return u == v
        def query_batch(self, pairs):
            p = np.asarray(pairs)
            return np.array([self.query(int(a), int(b)) for a, b in p], dtype=bool)
        @property
        def index_size_bytes(self): return 0

    all_names = catalog.methods()
    static_names = catalog.methods(kind="static")
    dynamic_names = catalog.methods(kind="dynamic")
    # The default lists everything; the two kinds partition it.
    assert sorted(static_names + dynamic_names) == sorted(all_names)
    assert set(static_names).isdisjoint(dynamic_names)
    assert "grail" in static_names
    assert "grail" not in dynamic_names
    assert "_dummy_dynamic" in dynamic_names
    assert "_dummy_dynamic" not in static_names


def test_unknown_kind_is_rejected():
    import pytest
    from pyreachability import catalog
    with pytest.raises(ValueError):
        catalog.methods(kind="sideways")
