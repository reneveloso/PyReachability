"""PyReachability — fast graph reachability methods (C++17 core, Python API).

Build a :class:`Graph`, pick a method (e.g. :class:`BFSDFS`), call ``build`` then
``query``. Methods share the :class:`ReachabilityIndex` interface and are discoverable
through :mod:`~pyreachability.catalog`.
"""
from ._version import __version__
from ._core import (Graph, _BFSDFSCore, _GRAILCore, _FelineCore, _PLLCore,
                    _TCCore, _TreeCoverCore, _BFLCore, _ChainCoverCore, _PReaCHCore,
                    _TwoHopCore, _TFLabelCore, _TOLCore, _HLCore, _OReachCore,
                    _ThreeHopCore, _PathHopCore, _FerrariCore, _DualLabelingCore,
                    _TreeSSPICore, _GRIPPCore, _PathTreeCore, _IPCore,
                    _OptimalChainCoverCore)
from .base import ReachabilityIndex
from . import catalog
from .static import (BFSDFS, TC,
                     TreeCover, GRAIL, TreeSSPI, DualLabeling, GRIPP,
                     PathTree, Ferrari,
                     PLL, TwoHop, ThreeHop, PathHop, TFLabel, DL, HL, TOL, OReach)   # temporary: removed in Task 5
import numpy as np


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
class BFL(ReachabilityIndex):
    """BFL: Bloom Filter Labeling — an approximate-transitive-closure partial index.

    Each vertex carries a DFS interval label plus two Bloom filters: one for the set it
    reaches (L_out) and one for the set that reaches it (L_in). The interval gives exact
    cuts for tree paths; the Bloom subset tests give exact *negative* cuts (no false
    negatives, but possible false positives), so inconclusive pairs fall back to a guided
    DFS. General graphs are reduced to a DAG via SCC condensation.

    Su, Zhu, Wei, Yu, *Reachability Querying: Can It Be Even Faster?*, IEEE TKDE 2017.

    Parameters
    ----------
    k : int, optional
        Number of 32-bit Bloom words per vertex per direction (default 5). More words →
        fewer false positives (less DFS) at the cost of ``2*k`` ints per node.
    seed : int, optional
        Seed for the Bloom hashing (default 1), for reproducibility.

    Examples
    --------
    >>> import numpy as np
    >>> from pyreachability import Graph, BFL
    >>> g = Graph.from_edges(np.array([0, 1], np.int32),
    ...                      np.array([1, 2], np.int32), num_nodes=3)
    >>> idx = BFL(); idx.build(g)
    >>> idx.query(0, 2)
    True
    """

    name = "bfl"

    def __init__(self, k: int = 5, seed: int = 1):
        self._core = _BFLCore(int(k), int(seed))
        self._built = False
        self.k = int(k)

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
class ChainCover(ReachabilityIndex):
    """Chain Cover: transitive-closure compression via chain (path) decomposition.

    The DAG is decomposed into chains (paths); each vertex has a ``(chain, position)``.
    Because a chain is a path, reaching a position implies reaching every later position on
    that chain, so each vertex records only the smallest reachable position per chain. ``u``
    reaches ``v`` iff ``u``'s recorded min position on ``v``'s chain is ≤ ``pos(v)``. A
    complete index; size depends on the DAG width. General graphs are reduced via SCC
    condensation.

    Jagadish, *A Compression Technique to Materialize Transitive Closure*, ACM TODS 1990.

    Examples
    --------
    >>> import numpy as np
    >>> from pyreachability import Graph, ChainCover
    >>> g = Graph.from_edges(np.array([0, 1], np.int32),
    ...                      np.array([1, 2], np.int32), num_nodes=3)
    >>> idx = ChainCover(); idx.build(g)
    >>> idx.query(0, 2)
    True
    """

    name = "chaincover"

    def __init__(self):
        self._core = _ChainCoverCore()
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
    >>> from pyreachability import Graph, PReaCH
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


@catalog.register
class IP(ReachabilityIndex):
    """IP: independent-permutation labels (approximate TC) + guided-search fallback.

    A partial index. For each of ``np`` random permutations, every vertex stores the ``k`` smallest
    permutation values of its reachable set ``Out`` and its reaching set ``In`` (k-min-wise). Since
    ``u`` reaches ``v`` requires ``Out(v) ⊆ Out(u)`` and ``In(u) ⊆ In(v)``, a permutation whose
    k-min labels prove one of these containments false answers the query negatively in constant
    time; a topological level filter adds another sound negative cut. Inconclusive queries fall
    back to a guided DFS that prunes with the same cuts, so the answer is always exact. General
    graphs are reduced via SCC condensation.

    Wei, Yu, Lu, Jin, *Reachability Querying: An Independent Permutation Labeling Approach*, PVLDB 2014.
    The k-min-wise scheme plus both of the paper's additional labels (Sec. 6): the Level label
    (forward + backward topological levels) and the Huge-Vertex label. Verified vs the BFS oracle.

    Parameters
    ----------
    k : int, optional
        Number of smallest values kept per permutation (default 2).
    np : int, optional
        Number of independent permutations (default 2). More cuts, more space.
    h : int, optional
        Max huge vertices stored per Huge-Vertex label (default 5; 0 disables it).
    mu : int, optional
        Out-degree threshold above which a vertex is "huge" (default 100, the paper's value).
    seed : int, optional
        RNG seed (default 1), for reproducibility.

    Examples
    --------
    >>> import numpy as np
    >>> from pyreachability import Graph, IP
    >>> g = Graph.from_edges(np.array([0, 1], np.int32),
    ...                      np.array([1, 2], np.int32), num_nodes=3)
    >>> idx = IP(); idx.build(g)
    >>> idx.query(0, 2)
    True
    """

    name = "ip"

    def __init__(self, k: int = 2, np: int = 2, h: int = 5, mu: int = 100, seed: int = 1):
        self._core = _IPCore(int(k), int(np), int(h), int(mu), int(seed))
        self._built = False
        self.k = int(k)

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
class OptimalChainCover(ReachabilityIndex):
    """Optimal Chain Cover: chain-cover compression over the *minimum* number of chains.

    Like :class:`ChainCover`, but the DAG is decomposed into the minimum number of chains (the DAG
    width, by Dilworth's theorem) instead of a greedy decomposition, giving smaller labels. The
    minimum decomposition is ``n`` minus a maximum bipartite matching over the reachability
    relation. Each vertex then gets a ``(chain, position)`` and records the smallest reachable
    position per chain; ``u`` reaches ``v`` iff ``u``'s recorded min position on ``v``'s chain is
    ``<= pos(v)``. A complete index. General graphs are reduced via SCC condensation.

    Chen & Chen, *An Efficient Algorithm for Answering Graph Reachability Queries*, ICDE 2008.
    (Minimum decomposition via textbook maximum bipartite matching rather than the paper's
    stratification + virtual-node procedure — same minimum chain count. Verified vs the BFS oracle.)

    Examples
    --------
    >>> import numpy as np
    >>> from pyreachability import Graph, OptimalChainCover
    >>> g = Graph.from_edges(np.array([0, 1], np.int32),
    ...                      np.array([1, 2], np.int32), num_nodes=3)
    >>> idx = OptimalChainCover(); idx.build(g)
    >>> idx.query(0, 2)
    True
    """

    name = "optchain"

    def __init__(self):
        self._core = _OptimalChainCoverCore()
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

    def num_chains(self) -> int:
        """Number of chains in the decomposition — equals the DAG's width (Dilworth's theorem)."""
        if not self._built:
            raise RuntimeError("index not built")
        return self._core.num_chains()


__all__ = ["__version__", "Graph", "ReachabilityIndex", "catalog",
           "BFSDFS", "GRAIL", "FELINE", "PLL", "TC", "TreeCover", "BFL",
           "ChainCover", "PReaCH", "TwoHop", "TFLabel", "TOL", "HL", "OReach",
           "ThreeHop", "PathHop", "Ferrari", "DualLabeling", "TreeSSPI", "GRIPP",
           "PathTree", "IP", "OptimalChainCover", "DL"]
