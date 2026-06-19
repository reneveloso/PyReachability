"""PyReachability — fast graph reachability methods (C++17 core, Python API).

Build a :class:`Graph`, pick a method (e.g. :class:`BFSDFS`), call ``build`` then
``query``. Methods share the :class:`ReachabilityIndex` interface and are discoverable
through :mod:`~pyreachability.catalog`.
"""
from ._version import __version__
from ._core import Graph, _BFSDFSCore, _GRAILCore
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


@catalog.register
class GRAIL(ReachabilityIndex):
    """GRAIL: scalable reachability via d randomized interval labels + guided search.

    A *partial* index. Each query is decided constant-time when possible by two exact
    cuts over the labels — a **negative cut** (containment) and a **positive cut** (PP:
    the target falls in the source's DFS-subtree interval) — plus a **topological level
    filter**. Only genuinely inconclusive pairs fall back to a label-guided, level-pruned
    DFS. General graphs are reduced to a DAG via SCC condensation.

    Yildirim, Chaoji, Zaki, *GRAIL: Scalable Reachability Index for Large Graphs*,
    PVLDB 3(1-2):276-284, 2010.

    Parameters
    ----------
    d : int, optional
        Number of interval-label dimensions (default 5). More dimensions sharpen the
        pruning (less DFS fallback) at the cost of ``2*d`` ints per node.
    seed : int, optional
        Seed for the randomized labeling (default 1), for reproducibility.

    Examples
    --------
    >>> import numpy as np
    >>> from pyreachability import Graph, GRAIL
    >>> g = Graph.from_edges(np.array([0, 1], np.int32),
    ...                      np.array([1, 2], np.int32), num_nodes=3)
    >>> idx = GRAIL(); idx.build(g)
    >>> idx.query(0, 2)
    True
    """

    name = "grail"

    def __init__(self, d: int = 5, seed: int = 1):
        self._core = _GRAILCore(int(d), int(seed))
        self._built = False
        self.d = int(d)

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
        return self._core.index_size_bytes()


__all__ = ["__version__", "Graph", "ReachabilityIndex", "catalog", "BFSDFS", "GRAIL"]
