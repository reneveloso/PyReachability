"""Methods the survey does not group into a labelled index class."""
import numpy as np

from .._core import _FelineCore, _PReaCHCore
from ..base import ReachabilityIndex
from .. import catalog


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
    >>> from pyreachability import Graph
    >>> from pyreachability.static import FELINE
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
class PReaCH(ReachabilityIndex):
    """PReaCH: Pruned Reachability Contraction Hierarchies.

    Builds an RCH ordering by contracting source/sink vertices (smallest input degree first);
    edges split into forward (order↑) and backward sets. A query is a bidirectional "up"
    search that must meet, pruned by forward/backward topological levels and single-DFS
    interval ranges. General graphs are reduced to a DAG via SCC condensation.

    Merz & Sanders, *PReaCH: A Fast Lightweight Reachability Index using Pruning and
    Contraction Hierarchies*, ESA 2014. (Ported from the paper; the extra empty/full DFS
    ranges of Lemmas 5-7 are omitted — they sharpen pruning, not correctness.)

    Examples
    --------
    >>> import numpy as np
    >>> from pyreachability import Graph
    >>> from pyreachability.static import PReaCH
    >>> g = Graph.from_edges(np.array([0, 1], np.int32),
    ...                      np.array([1, 2], np.int32), num_nodes=3)
    >>> idx = PReaCH(); idx.build(g)
    >>> idx.query(0, 2)
    True
    """

    name = "preach"

    def __init__(self):
        self._core = _PReaCHCore()
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
