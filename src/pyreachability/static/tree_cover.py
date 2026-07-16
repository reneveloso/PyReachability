"""Tree Cover class (survey section 3.1): interval labels from spanning trees."""
import numpy as np

from .._core import (_TreeCoverCore, _GRAILCore, _TreeSSPICore, _DualLabelingCore,
                     _GRIPPCore, _PathTreeCore, _FerrariCore)
from ..base import ReachabilityIndex
from .. import catalog


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
    >>> from pyreachability import Graph
    >>> from pyreachability.static import GRAIL
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
    >>> from pyreachability import Graph
    >>> from pyreachability.static import TreeCover
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
    >>> from pyreachability import Graph
    >>> from pyreachability.static import Ferrari
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
    >>> from pyreachability import Graph
    >>> from pyreachability.static import DualLabeling
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
    >>> from pyreachability import Graph
    >>> from pyreachability.static import TreeSSPI
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
    >>> from pyreachability import Graph
    >>> from pyreachability.static import GRIPP
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
    >>> from pyreachability import Graph
    >>> from pyreachability.static import PathTree
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


