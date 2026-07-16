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
from .static import BFSDFS, TC   # temporary: removed in Task 5
import numpy as np


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
class Ferrari(ReachabilityIndex):
    """Ferrari: budgeted exact/approximate interval labels + guided fallback (a partial index).

    A spanning tree is post-order numbered and each vertex's reachable set is encoded as a set of
    post-order id intervals (computed by merging children in reverse topological order). To stay
    within ``k`` intervals per vertex, adjacent intervals are merged across the smallest gaps,
    minimising false positives; an interval is *exact* if it contains no unreachable id, else
    *approximate*. A query checks the target id against the source's intervals: outside all ->
    not reachable; inside an exact one -> reachable; inside only approximate ones -> a guided DFS
    (with a topological level filter) settles it exactly. General graphs are reduced via SCC
    condensation.

    Seufert, Anand, Bedathur, Weikum, *FERRARI: Flexible and Efficient Reachability Range
    Assignment for Graph Indexing*, ICDE 2013. The tree-cover heuristic (parent = highest-tau
    in-neighbour), both indexing variants (Ferrari-L / Ferrari-G via ``c``), the GRAIL topological
    level filter, and seed-based pruning are all implemented. Independent implementation from the
    paper (reference code github.com/steps/Ferrari consulted); verified vs the BFS oracle.

    Parameters
    ----------
    k : int, optional
        Per-vertex interval budget (default 2). Larger ``k`` means more exact intervals (less
        DFS fallback) at the cost of more space; ``k=1`` is a single GRAIL-style range.
    c : int, optional
        Deferred-merging constant of the global variant (default 4, the paper's value). ``c=1``
        gives Ferrari-L (strict per-vertex budget); ``c>1`` gives Ferrari-G (global budget
        ``B=kn`` with finer labels where space allows).
    seeds : int, optional
        Number of max-degree seed vertices for the S+/S- pruning labels (default 32, max 64; 0
        disables seed pruning).

    Examples
    --------
    >>> import numpy as np
    >>> from pyreachability import Graph, Ferrari
    >>> g = Graph.from_edges(np.array([0, 1], np.int32),
    ...                      np.array([1, 2], np.int32), num_nodes=3)
    >>> idx = Ferrari(); idx.build(g)
    >>> idx.query(0, 2)
    True
    """

    name = "ferrari"

    def __init__(self, k: int = 2, c: int = 4, seeds: int = 32):
        self._core = _FerrariCore(int(k), int(c), int(seeds))
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
class DualLabeling(ReachabilityIndex):
    """Dual Labeling: spanning-tree intervals + a transitive link table (best for sparse graphs).

    A spanning tree is preorder interval-labeled, so tree reachability is an interval containment.
    The remaining (non-tree) reachability is carried by the *transitive link table*: each non-tree
    edge ``(tail, head)`` becomes a link ``pre(tail) -> [head interval]`` (superfluous ones
    dropped), closed under composition. ``u`` reaches ``v`` iff ``v`` falls in ``u``'s tree
    interval, or some link ``i -> [j, k)`` has ``i`` in ``u``'s interval and ``pre(v)`` in
    ``[j, k)``. A complete index of size ``O(n + t^2)`` in the number ``t`` of non-tree edges, so
    it shines when the graph is nearly a tree. General graphs are reduced via SCC condensation.

    Wang, He, Yang, Yu, Yu, *Dual Labeling: Answering Graph Reachability Queries in Constant
    Time*, ICDE 2006. (Faithful to Theorem 1; the O(1) TLC-counting accelerator with
    gridding/snapping is represented by a direct scan of the small link table, and a plain DFS
    spanning tree is used. Verified vs the BFS oracle.)

    Examples
    --------
    >>> import numpy as np
    >>> from pyreachability import Graph, DualLabeling
    >>> g = Graph.from_edges(np.array([0, 1], np.int32),
    ...                      np.array([1, 2], np.int32), num_nodes=3)
    >>> idx = DualLabeling(); idx.build(g)
    >>> idx.query(0, 2)
    True
    """

    name = "dual"

    def __init__(self):
        self._core = _DualLabelingCore()
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
class TreeSSPI(ReachabilityIndex):
    """Tree+SSPI: tree-cover intervals + a Surrogate & Surplus Predecessor Index.

    A spanning tree is preorder interval-labeled, so tree ("ppure") reachability is interval
    containment. The remaining reachability (paths through non-tree edges) is carried by the SSPI:
    each vertex keeps a predecessor list of the tails of its non-tree in-edges. ``x`` reaches
    ``y`` iff ``x`` is a tree-ancestor of ``y``, or — searching the SSPI transitively, with
    predecessor inheritance along tree ancestors — some predecessor reachable to ``y`` is itself
    tree-reached by ``x``. A complete index (always exact, via an online guided search for the
    non-tree paths), compact for sparse graphs. General graphs are reduced via SCC condensation.

    Chen, Gupta, Kurul, *Stack-based Algorithms for Pattern Matching on DAGs*, VLDB 2005. (The
    SSPI stores own non-tree in-edge tails with inheritance resolved at query time; a plain DFS
    spanning tree is used. Verified vs the BFS oracle.)

    Examples
    --------
    >>> import numpy as np
    >>> from pyreachability import Graph, TreeSSPI
    >>> g = Graph.from_edges(np.array([0, 1], np.int32),
    ...                      np.array([1, 2], np.int32), num_nodes=3)
    >>> idx = TreeSSPI(); idx.build(g)
    >>> idx.query(0, 2)
    True
    """

    name = "sspi"

    def __init__(self):
        self._core = _TreeSSPICore()
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
class GRIPP(ReachabilityIndex):
    """GRIPP: pre/postorder order-tree instances + the hop technique (online guided search).

    A DFS builds the *order tree*: each node gets one instance per incoming edge — the first is
    its *tree instance* (recursed), the rest are *non-tree instance* leaves — each with a pre/post
    interval. The reachable instance set ``RIS(v)`` is the subtree of ``v``'s tree instance. ``v``
    reaches ``w`` iff some instance of ``w`` falls in ``RIS(v)``; otherwise each non-tree instance
    in ``RIS(v)`` marks a *hop node* whose own RIS is searched recursively (a guided DFS over hop
    nodes). A complete index of size ``O(n + m)`` with an online search. General graphs are reduced
    via SCC condensation.

    Trißl & Leser, *Fast and Practical Indexing and Querying of Very Large Graphs*, SIGMOD 2007.
    (The hop technique with basic hop-node pruning; the paper's advanced relative-position pruning
    is omitted as a speed optimisation. Verified vs the BFS oracle.)

    Examples
    --------
    >>> import numpy as np
    >>> from pyreachability import Graph, GRIPP
    >>> g = Graph.from_edges(np.array([0, 1], np.int32),
    ...                      np.array([1, 2], np.int32), num_nodes=3)
    >>> idx = GRIPP(); idx.build(g)
    >>> idx.query(0, 2)
    True
    """

    name = "gripp"

    def __init__(self):
        self._core = _GRIPPCore()
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
class PathTree(ReachabilityIndex):
    """Path-Tree: a path-tree cover (generalized tree cover) + residual transitive closure.

    The DAG is decomposed into paths; the paths form a path-graph whose spanning arborescence (the
    SP-tree) defines the *path-tree cover*. Each vertex gets a 3-tuple ``(X, I.begin, I.end)`` — an
    X label from a post-order DFS over the cover and the SP-tree interval ``I`` of its path — so
    that ``u`` reaches ``v`` *within the cover* iff ``X(u) <= X(v)`` and ``v``'s interval is
    contained in ``u``'s. Reachability not captured by the cover is compressed into a per-vertex
    residual set ``Rc(u)``; ``u`` reaches ``v`` iff the cover says so or some ``x`` in ``Rc(u)``
    cover-reaches ``v``. A complete index. General graphs are reduced via SCC condensation.

    Jin, Ruan, Xiang, Wang, *Path-Tree: An Efficient Reachability Indexing Scheme for Large
    Directed Graphs*, ACM TODS 2011. (Independent implementation; the minimal-equivalent-edge-set
    step is skipped, the SP-tree is a greedy spanning arborescence vs Edmonds' maximum-weight one,
    and the residual is scanned linearly. Verified vs the BFS oracle.)

    Examples
    --------
    >>> import numpy as np
    >>> from pyreachability import Graph, PathTree
    >>> g = Graph.from_edges(np.array([0, 1], np.int32),
    ...                      np.array([1, 2], np.int32), num_nodes=3)
    >>> idx = PathTree(); idx.build(g)
    >>> idx.query(0, 2)
    True
    """

    name = "pathtree"

    def __init__(self):
        self._core = _PathTreeCore()
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
