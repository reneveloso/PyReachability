"""Baselines (survey section 2.2): online traversal and materialised TC."""
import numpy as np

from .._core import _BFSDFSCore, _TCCore
from ..base import ReachabilityIndex
from .. import catalog


@catalog.register
class BFSDFS(ReachabilityIndex):
    """Online reachability by graph traversal — the baseline and correctness oracle.

    Builds no index: each :meth:`query` runs a BFS over the graph, so queries
    are O(V + E) but there is zero construction cost or memory overhead. Every
    indexing method in the catalog is validated against this method.

    Examples
    --------
    >>> import numpy as np
    >>> from pyreachability import Graph, BFSDFS
    >>> g = Graph.from_edges(np.array([0, 1], np.int32),
    ...                      np.array([1, 2], np.int32), num_nodes=3)
    >>> idx = BFSDFS(); idx.build(g)
    >>> idx.query(0, 2)
    True
    """

    name = "bfsdfs"

    def __init__(self):
        self._core = _BFSDFSCore()
        self._built = False

    def build(self, graph) -> None:
        self._core.build(graph)
        self._built = True

    def query(self, u: int, v: int) -> bool:
        if not self._built:
            raise RuntimeError("index not built")
        return bool(self._core.query(int(u), int(v)))

    def query_batch(self, pairs) -> np.ndarray:
        if not self._built:
            raise RuntimeError("index not built")
        return self._core.query_batch(pairs)

    @property
    def index_size_bytes(self) -> int:
        return 0


@catalog.register
class TC(ReachabilityIndex):
    """TC: full transitive closure materialized as per-vertex bitsets (Warshall-style).

    Query is a single O(1) bit test, but the index is O(V^2 / 64), so this is a baseline
    for small graphs only. General graphs are reduced to a DAG via SCC condensation.

    Warshall, *A Theorem on Boolean Matrices*, JACM 9(1):11-12, 1962.

    Examples
    --------
    >>> import numpy as np
    >>> from pyreachability import Graph, TC
    >>> g = Graph.from_edges(np.array([0, 1], np.int32),
    ...                      np.array([1, 2], np.int32), num_nodes=3)
    >>> idx = TC(); idx.build(g)
    >>> idx.query(0, 2)
    True
    """

    name = "tc"

    def __init__(self):
        self._core = _TCCore()
        self._built = False

    def build(self, graph) -> None:
        self._core.build(graph)
        self._built = True

    def query(self, u: int, v: int) -> bool:
        if not self._built:
            raise RuntimeError("index not built")
        return bool(self._core.query(int(u), int(v)))

    def query_batch(self, pairs) -> np.ndarray:
        if not self._built:
            raise RuntimeError("index not built")
        return self._core.query_batch(pairs)

    @property
    def index_size_bytes(self) -> int:
        return self._core.index_size_bytes()
