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
                     PathTree, Ferrari)   # temporary: removed in Task 5
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

    A vertex hierarchy ``V0 ⊃ V1 ⊃ ... ⊃ Vh`` is built where each level is the one-side
    reachability backbone of the previous one, discovered by FastCover (Jin et al., SCARAB,
    SIGMOD 2012) with locality threshold ``eps``. The core graph is labeled with a 2-hop labeling
    and labels propagate down (Algorithm 1, Formulas 4-5): for ``v`` at level ``i``,
    ``label_out(v)`` is its ``ceil(eps/2)``-hop out-neighbours in ``G_i`` plus the union of
    ``label_out`` of its nearest backbone vertices ``Bout^eps(v)``, and symmetrically for
    ``label_in``. ``u`` reaches ``v`` iff the two sets intersect. Unlike PLL/TOL this uses a
    *hierarchy* rather than a flat vertex order. A complete index. General graphs are reduced via
    SCC condensation.

    Jin & Wang, *Simple, Fast, and Scalable Reachability Oracle*, PVLDB 6(14), 2013, with the
    FastCover backbone of Jin, Ruan, Dey & Yu, *SCARAB*, SIGMOD 2012. Default ``eps=2`` (the
    paper's default); verified vs the BFS oracle.

    Parameters
    ----------
    eps : int, optional
        Locality threshold of the backbone (default 2, the paper's default). Smaller ``eps``
        gives larger but cheaper-to-build labels.

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

    def __init__(self, eps: int = 2):
        self._core = _HLCore(eps)
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

    def two_hop_labels(self):
        """The built Lin/Lout labels per original vertex (DAG inputs only).

        Only defined when every SCC is a singleton (the input is a DAG), so
        condensed-DAG ids map 1:1 back to original vertices. Used by the
        paper-example fidelity suite (``tests/paper_examples/``)."""
        if not self._built:
            raise RuntimeError("index not built")
        comp, lin, lout = self._core.labels()
        n = len(comp)
        if len(set(comp.tolist())) != n:
            raise NotImplementedError("two_hop_labels() requires a DAG input")
        # comp[v] = condensed id of vertex v; invert to translate label entries back
        rep = {int(c): v for v, c in enumerate(comp.tolist())}
        return {
            v: {"Lin": {rep[int(e)] for e in lin[comp[v]]},
                "Lout": {rep[int(e)] for e in lout[comp[v]]}}
            for v in range(n)
        }


@catalog.register
class OReach(ReachabilityIndex):
    """O'Reach: constant-time observations + guided-search fallback (a partial index).

    A battery of sound constant-time tests resolves most queries (in the paper's order):
    forward/backward topological levels (negative), ``k`` *supportive vertices* with full
    out/in-reachability stored as bitmasks (one positive and two negative observations), ``t``
    extended topological orderings carrying high/max (or low/min) indices (positive and negative),
    and a weakly-connected-component check (negative). Inconclusive queries fall back to a pruning
    *bidirectional* BFS that applies the same observations to each newly seen vertex — shortcutting
    on a definitive-positive test and pruning on a definitive-negative one — so the answer is always
    exact. General graphs are reduced via SCC condensation.

    Hanauer, Schulz, Trummer, *O'Reach: Even Faster Reachability in Large Graphs*, SEA 2021.
    Faithful: supportive vertices use the paper's slim-level selection (top-k by |R⁺|·|R⁻|),
    orderings start from sources, and the fallback is the pruning bidirectional BFS. Verified vs
    the BFS oracle.

    Parameters
    ----------
    k : int, optional
        Number of supportive vertices (default 16, capped at 64).
    p : int, optional
        Candidates-per-support multiplier for selection (default 75; candidate set size ≈ ``kp``).
    h : int, optional
        Slim-level threshold (default 8): a topological level with ≤ ``h`` vertices is "slim" and
        its vertices become supportive-vertex candidates.
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

    def __init__(self, k: int = 16, p: int = 75, h: int = 8, t: int = 4, seed: int = 1):
        self._core = _OReachCore(int(k), int(p), int(h), int(t), int(seed))
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


@catalog.register
class ThreeHop(ReachabilityIndex):
    """3-Hop: high-compression reachability via chains as highways.

    The DAG is decomposed into chains; ``u`` reaches ``v`` in three hops through an intermediate
    chain ``C`` — ``u`` -> entry point on ``C``, along ``C`` to an exit point, exit -> ``v`` —
    i.e. iff some chain ``C`` has an entry recorded for ``u`` preceding an exit recorded for
    ``v``. Construction follows the paper: the *transitive closure contour* (pseudo-diagonal
    cells of the chain-pair reachability submatrices) is covered by a greedy *factorization*
    that repeatedly picks the chain whose chain-center bipartite graph has the densest subgraph,
    recording entry/exit anchors. Queries resolve a vertex's entry/exit on a highway via its
    nearest anchor along its own chain. A complete index. General graphs are reduced via SCC
    condensation.

    Jin, Xiang, Ruan, Fuhry, *3-HOP: A High-Compression Indexing Scheme for Reachability
    Query*, SIGMOD 2009. (Densest subgraph via the endorsed linear 2-approximation; construction
    uses transitive-closure bitsets, so this targets small/medium graphs. Verified vs the BFS
    oracle.)

    Examples
    --------
    >>> import numpy as np
    >>> from pyreachability import Graph, ThreeHop
    >>> g = Graph.from_edges(np.array([0, 1], np.int32),
    ...                      np.array([1, 2], np.int32), num_nodes=3)
    >>> idx = ThreeHop(); idx.build(g)
    >>> idx.query(0, 2)
    True
    """

    name = "3hop"

    def __init__(self):
        self._core = _ThreeHopCore()
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
class PathHop(ReachabilityIndex):
    """Path-Hop: high-compression reachability with trees as highways.

    The tree-cover analogue of :class:`ThreeHop`. A spanning tree (tree cover) is interval-
    labeled so that tree reachability is interval containment. The *residual transitive closure*
    (reachable pairs not captured by the tree, as each vertex's reachable non-tree subtree roots)
    is covered by a greedy set cover of *path-hops* ``x ; y`` (``x`` a tree-ancestor of ``y``):
    ``x`` is added to ``L_out`` of ``Pred(x)`` and ``y`` to ``L_in`` of ``Succ(y)``. A query
    ``reach(u, v)`` is true iff ``v`` is in ``u``'s subtree, or some ``x`` in ``L_out(u) U {u}``
    is a tree-ancestor of some ``y`` drawn from ``L_in`` of ``v`` and its tree ancestors. A
    complete index. General graphs are reduced via SCC condensation.

    Cai & Poon, *Path-Hop: Efficiently Indexing Large Graphs for Reachability Queries*, CIKM
    2010. (A DFS spanning forest is used as the tree cover, vs the paper's optimal tree cover;
    construction materialises reachable-root sets, so this targets small/medium graphs. Verified
    vs the BFS oracle.)

    Examples
    --------
    >>> import numpy as np
    >>> from pyreachability import Graph, PathHop
    >>> g = Graph.from_edges(np.array([0, 1], np.int32),
    ...                      np.array([1, 2], np.int32), num_nodes=3)
    >>> idx = PathHop(); idx.build(g)
    >>> idx.query(0, 2)
    True
    """

    name = "pathhop"

    def __init__(self):
        self._core = _PathHopCore()
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
class DL(ReachabilityIndex):
    """DL: Distribution Labeling — a 2-hop oracle equivalent to PLL.

    Distribution-Labeling (Jin & Wang, 2013, Algorithm 2) ranks vertices by a total order and
    then, for each vertex in turn, *distributes* it into the ``L_out``/``L_in`` of the vertices it
    connects, adding it only where it covers a still-uncovered reachable pair (a pruned reverse/
    forward BFS). With the paper's recommended rank ``(|N_out(v)|+1)·(|N_in(v)|+1)`` this is exactly
    the pruned-landmark-labeling construction of :class:`PLL`, and the CSUR 2025 survey proves DL
    and PLL produce equivalent indexes. It is therefore built on the same shared 2-hop framework as
    PLL (identical labels); it is exposed as a distinct catalog entry for completeness. A complete
    index. General graphs are reduced via SCC condensation.

    Jin & Wang, *Simple, Fast, and Scalable Reachability Oracle*, PVLDB 6(14), 2013 (the same paper
    as :class:`HL`). Verified vs the BFS oracle.

    Examples
    --------
    >>> import numpy as np
    >>> from pyreachability import Graph, DL
    >>> g = Graph.from_edges(np.array([0, 1], np.int32),
    ...                      np.array([1, 2], np.int32), num_nodes=3)
    >>> idx = DL(); idx.build(g)
    >>> idx.query(0, 2)
    True
    """

    name = "dl"

    def __init__(self):
        self._core = _PLLCore()   # Distribution-Labeling == PLL (survey-proven; identical labels)
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
