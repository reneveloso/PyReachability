"""PyReachability — fast graph reachability methods (C++17 core, Python API).

Build a :class:`Graph`, pick a method (e.g. :class:`BFSDFS`), call ``build`` then
``query``. Methods share the :class:`ReachabilityIndex` interface and are discoverable
through :mod:`~pyreachability.catalog`.
"""
from ._version import __version__
from ._core import (Graph, _BFSDFSCore, _GRAILCore, _FelineCore, _PLLCore,
                    _TCCore, _TreeCoverCore, _BFLCore, _ChainCoverCore, _PReaCHCore,
                    _TwoHopCore, _TFLabelCore, _TOLCore, _HLCore, _OReachCore)
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
class TwoHop(ReachabilityIndex):
    """2-Hop labeling: the original near-minimum 2-hop cover.

    Each vertex keeps ``L_out`` (centers it can reach) and ``L_in`` (centers that reach it);
    ``u`` reaches ``v`` iff the two sets share a center. The cover is built by the greedy
    set-cover of Cohen et al.: each step adds the *center* whose bipartite "center graph" of
    still-uncovered pairs has the densest subgraph (found by the linear-time 2-approximation
    that repeatedly drops the minimum-degree vertex). A complete index with near-minimum label
    size. Minimum 2-hop is NP-hard, so the build is a (logarithmic-factor) heuristic and is
    expensive — a small/medium-graph method, like :class:`TC` / :class:`TreeCover`. General
    graphs are reduced via SCC condensation.

    Cohen, Halperin, Kaplan, Zwick, *Reachability and Distance Queries via 2-Hop Labels*,
    SIAM J. Comput. 32(5):1338-1355, 2003. (Ported from the paper; verified vs the BFS oracle.)

    Examples
    --------
    >>> import numpy as np
    >>> from pyreachability import Graph, TwoHop
    >>> g = Graph.from_edges(np.array([0, 1], np.int32),
    ...                      np.array([1, 2], np.int32), num_nodes=3)
    >>> idx = TwoHop(); idx.build(g)
    >>> idx.query(0, 2)
    True
    """

    name = "twohop"

    def __init__(self):
        self._core = _TwoHopCore()
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
class TFLabel(ReachabilityIndex):
    """TF-Label: 2-hop labeling built by topological folding.

    Vertices are placed on topological levels and the DAG is folded in half repeatedly — each
    fold removes the odd-level vertices and reconnects their in-neighbours directly to their
    out-neighbours — so each vertex is processed in O(lg L) folds rather than all L levels.
    ``label_out``/``label_in`` are then the recursive closures of Definition 5 over the folding
    graphs, and ``u`` reaches ``v`` iff the two sets intersect. A complete index. Cross-level
    edges are made level-consecutive by edge subdivision (faithful to the folding scheme, but
    larger labels than the paper's shared-dummy optimisation), so it targets small/medium
    graphs. General graphs are reduced via SCC condensation.

    Cheng, Huang, Wu, Fu, *TF-Label: a Topological-Folding Labeling Scheme for Reachability
    Querying in a Large Graph*, SIGMOD 2013. (Ported from the paper; verified vs the BFS oracle.)

    Examples
    --------
    >>> import numpy as np
    >>> from pyreachability import Graph, TFLabel
    >>> g = Graph.from_edges(np.array([0, 1], np.int32),
    ...                      np.array([1, 2], np.int32), num_nodes=3)
    >>> idx = TFLabel(); idx.build(g)
    >>> idx.query(0, 2)
    True
    """

    name = "tfl"

    def __init__(self):
        self._core = _TFLabelCore()
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
class TOL(ReachabilityIndex):
    """TOL: Total Order Labeling — the 2-hop framework generalizing PLL.

    A strict total order of the vertices uniquely determines a canonical 2-hop index, built by
    the shared pruned-BFS labeling. TOL's contribution is the *contribution-score* order:
    ``f(v) = (a*b + a + b) / (a + b)`` with ``a = |ancestors(v)|`` and ``b = |descendants(v)|``
    (a vertex covering many reachable pairs ranks highest). The exact scores need transitive
    closure, so they are approximated by a single linear scan of the DAG, then vertices are
    ordered by descending ``f``. ``u`` reaches ``v`` iff ``label_out(u)`` and ``label_in(v)``
    intersect. A complete index. General graphs are reduced via SCC condensation.

    Zhu, Lin, Wang, Xiao, *Reachability Queries on Large Dynamic Graphs: A Total Order
    Approach*, SIGMOD 2014. (Labeling = shared 2-hop framework; the contribution-score order is
    TOL-specific. Verified vs the BFS oracle.)

    Examples
    --------
    >>> import numpy as np
    >>> from pyreachability import Graph, TOL
    >>> g = Graph.from_edges(np.array([0, 1], np.int32),
    ...                      np.array([1, 2], np.int32), num_nodes=3)
    >>> idx = TOL(); idx.build(g)
    >>> idx.query(0, 2)
    True
    """

    name = "tol"

    def __init__(self):
        self._core = _TOLCore()
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
class HL(ReachabilityIndex):
    """HL: Hierarchical Labeling — a 2-hop oracle from a recursive reachability backbone.

    A vertex hierarchy ``V0 ⊃ V1 ⊃ ... ⊃ Vh`` is built where each level is the reachability
    backbone of the previous one (with ``eps=1`` the backbone is a vertex cover). The core is
    labeled first and labels propagate down: for ``v`` at level ``i``, ``label_out(v)`` is ``v``
    plus the union of ``label_out`` of its out-neighbours in ``G_i`` (all of which sit in the
    backbone), and symmetrically for ``label_in``. ``u`` reaches ``v`` iff the two sets
    intersect. Unlike PLL/TOL this uses a *hierarchy* rather than a flat vertex order, and needs
    no transitive closure. A complete index. General graphs are reduced via SCC condensation.

    Jin & Wang, *Simple, Fast, and Scalable Reachability Oracle*, PVLDB 6(14), 2013. (Ported
    from the paper with locality ``eps=1`` — a vertex-cover backbone, vs the paper's ``eps=2``
    FastCover; verified vs the BFS oracle.)

    Examples
    --------
    >>> import numpy as np
    >>> from pyreachability import Graph, HL
    >>> g = Graph.from_edges(np.array([0, 1], np.int32),
    ...                      np.array([1, 2], np.int32), num_nodes=3)
    >>> idx = HL(); idx.build(g)
    >>> idx.query(0, 2)
    True
    """

    name = "hl"

    def __init__(self):
        self._core = _HLCore()
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
class OReach(ReachabilityIndex):
    """O'Reach: constant-time observations + guided-search fallback (a partial index).

    A battery of sound constant-time tests resolves most queries: forward/backward topological
    levels (negative), ``k`` *supportive vertices* with full out/in-reachability stored as
    bitmasks (one positive and two negative observations), and ``t`` extended topological
    orderings carrying high/max (or low/min) indices (positive and negative). Inconclusive
    queries fall back to a guided DFS that prunes on a definitive-negative test and shortcuts on
    a definitive-positive one, so the answer is always exact. General graphs are reduced via SCC
    condensation.

    Hanauer, Schulz, Trummer, *O'Reach: Even Faster Reachability in Large Graphs*, SEA 2021.
    (Supportive-vertex selection is a simplified central-level heuristic; the fallback is a
    guided DFS rather than a pruned bidirectional BFS. Verified vs the BFS oracle.)

    Parameters
    ----------
    k : int, optional
        Number of supportive vertices (default 16, capped at 64).
    p : int, optional
        Candidate multiplier for supportive-vertex selection (default 50).
    t : int, optional
        Number of extended topological orderings (default 4; even = forward, odd = reverse).
    seed : int, optional
        RNG seed for ordering randomization (default 1), for reproducibility.

    Examples
    --------
    >>> import numpy as np
    >>> from pyreachability import Graph, OReach
    >>> g = Graph.from_edges(np.array([0, 1], np.int32),
    ...                      np.array([1, 2], np.int32), num_nodes=3)
    >>> idx = OReach(); idx.build(g)
    >>> idx.query(0, 2)
    True
    """

    name = "oreach"

    def __init__(self, k: int = 16, p: int = 50, t: int = 4, seed: int = 1):
        self._core = _OReachCore(int(k), int(p), int(t), int(seed))
        self._built = False
        self.k = int(k)
        self.t = int(t)

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
           "BFSDFS", "GRAIL", "FELINE", "PLL", "TC", "TreeCover", "BFL",
           "ChainCover", "PReaCH", "TwoHop", "TFLabel", "TOL", "HL", "OReach"]
