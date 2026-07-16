"""2-Hop class (survey section 3.2): per-vertex L_in / L_out label sets."""
import numpy as np

from .._core import (_PLLCore, _TwoHopCore, _ThreeHopCore, _PathHopCore,
                     _TFLabelCore, _HLCore, _TOLCore, _OReachCore)
from ..base import ReachabilityIndex
from .. import catalog


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
    >>> from pyreachability import Graph
    >>> from pyreachability.static import PLL
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
    >>> from pyreachability import Graph
    >>> from pyreachability.static import TwoHop
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
    >>> from pyreachability import Graph
    >>> from pyreachability.static import TFLabel
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
    >>> from pyreachability import Graph
    >>> from pyreachability.static import TOL
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
    >>> from pyreachability import Graph
    >>> from pyreachability.static import HL
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
    >>> from pyreachability import Graph
    >>> from pyreachability.static import OReach
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
    >>> from pyreachability import Graph
    >>> from pyreachability.static import ThreeHop
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
    >>> from pyreachability import Graph
    >>> from pyreachability.static import PathHop
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
    >>> from pyreachability import Graph
    >>> from pyreachability.static import DL
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
