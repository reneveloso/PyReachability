"""PyReachability — fast graph reachability methods (C++17 core, Python API).

Build a :class:`Graph`, pick a method (e.g. :class:`BFSDFS`), call ``build`` then
``query``. Methods share the :class:`ReachabilityIndex` interface and are discoverable
through :mod:`~pyreachability.catalog`.
"""
from ._version import __version__
from ._core import Graph, _BFSDFSCore
from .base import ReachabilityIndex
from . import catalog
import numpy as np


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
        p = np.ascontiguousarray(pairs, dtype=np.int32).reshape(-1, 2)
        out = np.empty(p.shape[0], dtype=bool)
        for i in range(p.shape[0]):
            out[i] = self.query(int(p[i, 0]), int(p[i, 1]))
        return out

    @property
    def index_size_bytes(self) -> int:
        return 0


__all__ = ["__version__", "Graph", "ReachabilityIndex", "catalog", "BFSDFS"]
