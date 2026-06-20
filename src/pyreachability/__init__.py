"""PyReachability — fast graph reachability methods (C++17 core, Python API).

Build a :class:`Graph`, pick a method (e.g. :class:`BFSDFS`), call ``build`` then
``query``. Methods share the :class:`ReachabilityIndex` interface and are discoverable
through :mod:`~pyreachability.catalog`.
"""
from ._version import __version__
from ._core import (Graph, _BFSDFSCore, _GRAILCore, _FelineCore, _PLLCore,
                    _TCCore, _TreeCoverCore)
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
        if not self._built:
            raise RuntimeError("index not built")
        return self._core.query_batch(pairs)

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
    bidirectional : bool, optional
        If True, inconclusive queries use a two-sided (forward + backward) search
        instead of a one-sided guided DFS — faster on hard pairs, at the cost of an
        extra reverse-edge array. Default False (keeps the index lean).

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

    def __init__(self, d: int = 5, seed: int = 1, bidirectional: bool = False):
        self._core = _GRAILCore(int(d), int(seed), bool(bidirectional))
        self._built = False
        self.d = int(d)
        self.bidirectional = bool(bidirectional)

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


@catalog.register
class FELINE(ReachabilityIndex):
    """FELINE: Fast rEfined onLINE search via a 2D dominance drawing.

    Each vertex gets a coordinate (X, Y) from two topological orderings; the second
    is built so the two orders are complementary (Kornaropoulos heuristic), minimizing
    false positives. Reachability implies dominance — ``X[u] <= X[v] and Y[u] <= Y[v]``
    — so a failed componentwise test is an exact O(1) negative answer; inconclusive
    pairs fall back to a dominance-pruned DFS. The index is linear, O(|V|). General
    graphs are reduced to a DAG via SCC condensation.

    Constant-time filters layered before any search: the positive-cut (a min-post
    spanning-tree interval — a contained interval means a tree path, an exact positive)
    and the topological level filter. Inconclusive pairs fall back to a pruned DFS.

    Veloso, Cerf, Meira Jr., Zaki, *Reachability Queries in Very Large Graphs: A Fast
    Refined Online Search Approach*, EDBT 2014, pp. 511-522. This is the canonical
    reference implementation of FELINE (authored by a paper author), validated to agree
    with the original 2014 code on 100% of a 500k-query test.

    Parameters
    ----------
    bidirectional : bool, optional
        If True (FELINE-B), also index the reversed graph for a second dominance test that
        prunes from the target side too — faster on hard pairs, at the cost of a second
        coordinate pair and a reverse CSR. Default False.

    Examples
    --------
    >>> import numpy as np
    >>> from pyreachability import Graph, FELINE
    >>> g = Graph.from_edges(np.array([0, 1], np.int32),
    ...                      np.array([1, 2], np.int32), num_nodes=3)
    >>> idx = FELINE(); idx.build(g)
    >>> idx.query(0, 2)
    True
    """

    name = "feline"

    def __init__(self, bidirectional: bool = False):
        self._core = _FelineCore(bool(bidirectional))
        self._built = False
        self.bidirectional = bool(bidirectional)

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


@catalog.register
class PLL(ReachabilityIndex):
    """PLL: Pruned Landmark Labeling — a 2-hop reachability index.

    Each vertex keeps two sorted landmark sets — the landmarks it reaches (L_out) and the
    landmarks that reach it (L_in), built by pruned BFS in a canonical (degree-product)
    order. ``u`` reaches ``v`` iff L_out(u) and L_in(v) share a landmark, so queries are a
    sorted-list intersection with **no fallback search** (a complete index). General graphs
    are reduced to a DAG via SCC condensation.

    This implements the 2-hop *pruned landmark labeling* variant only; the 3-hop *pruned path
    labeling* from the same paper (and its reference implementation) is not included.

    Yano, Akiba, Iwata, Yoshida, *Fast and Scalable Reachability Queries on Graphs by Pruned
    Labeling with Landmarks and Paths*, CIKM 2013.

    Examples
    --------
    >>> import numpy as np
    >>> from pyreachability import Graph, PLL
    >>> g = Graph.from_edges(np.array([0, 1], np.int32),
    ...                      np.array([1, 2], np.int32), num_nodes=3)
    >>> idx = PLL(); idx.build(g)
    >>> idx.query(0, 2)
    True
    """

    name = "pll"

    def __init__(self):
        self._core = _PLLCore()
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


@catalog.register
class TreeCover(ReachabilityIndex):
    """Tree Cover: transitive-closure compression via DFS post-order interval labels.

    A DFS spanning forest numbers vertices in post-order; the post-order numbers reachable
    from a vertex are stored as merged intervals (tree descendants are contiguous). ``u``
    reaches ``v`` iff ``post(v)`` lies in one of ``u``'s intervals. A compression baseline
    (index size depends on the number of non-tree edges). General graphs are reduced to a
    DAG via SCC condensation.

    Agrawal, Borgida, Jagadish, *Efficient Management of Transitive Relationships in Large
    Data and Knowledge Bases*, SIGMOD 1989, pp. 253-262.

    Examples
    --------
    >>> import numpy as np
    >>> from pyreachability import Graph, TreeCover
    >>> g = Graph.from_edges(np.array([0, 1], np.int32),
    ...                      np.array([1, 2], np.int32), num_nodes=3)
    >>> idx = TreeCover(); idx.build(g)
    >>> idx.query(0, 2)
    True
    """

    name = "treecover"

    def __init__(self):
        self._core = _TreeCoverCore()
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


__all__ = ["__version__", "Graph", "ReachabilityIndex", "catalog",
           "BFSDFS", "GRAIL", "FELINE", "PLL", "TC", "TreeCover"]
