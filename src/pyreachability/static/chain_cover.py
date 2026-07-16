"""Chain Cover class (survey section 3.1.5): chain decompositions."""
import numpy as np

from .._core import _ChainCoverCore, _OptimalChainCoverCore
from ..base import ReachabilityIndex
from .. import catalog


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
