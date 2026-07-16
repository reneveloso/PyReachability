"""Approximate TC class (survey section 3.3): sketch labels + guided DFS."""
import numpy as np

from .._core import _IPCore, _BFLCore
from ..base import ReachabilityIndex
from .. import catalog


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
    >>> from pyreachability import Graph
    >>> from pyreachability.static import BFL
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
class IP(ReachabilityIndex):
    """IP: independent-permutation labels (approximate TC) + guided-search fallback.

    A partial index. For each of ``num_perm`` random permutations, every vertex stores the ``k`` smallest
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
    num_perm : int, optional
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
    >>> from pyreachability import Graph
    >>> from pyreachability.static import IP
    >>> g = Graph.from_edges(np.array([0, 1], np.int32),
    ...                      np.array([1, 2], np.int32), num_nodes=3)
    >>> idx = IP(); idx.build(g)
    >>> idx.query(0, 2)
    True
    """

    name = "ip"

    def __init__(self, k: int = 2, num_perm: int = 2, h: int = 5, mu: int = 100, seed: int = 1):
        self._core = _IPCore(int(k), int(num_perm), int(h), int(mu), int(seed))
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
