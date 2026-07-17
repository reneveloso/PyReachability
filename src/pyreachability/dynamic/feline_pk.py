"""Feline-PK: the wrapper around the incrementally maintained Cython core."""
import numpy as np

from .._core import _FelinePKCore
from .. import catalog
from .base import (DynamicReachabilityIndex, EDGE_INSERT, EDGE_DELETE,
                    VERTEX_INSERT, VERTEX_DELETE)


@catalog.register
class FelinePK(DynamicReachabilityIndex):
    """Feline-PK: FELINE's index maintained incrementally under graph updates.

    Keeps the two topological orderings (the X/Y dominance drawing) as the graph
    changes, instead of rebuilding. Unlike the static half, the SCC condensation
    is not a one-shot Tarjan pass done by the caller: Feline-PK maintains it
    itself, folding a component when an inserted edge closes a cycle and
    splitting one when a removed edge breaks it. Coordinates are gap-tolerant
    integers, so a removal is O(1) and leaves a gap rather than compacting.

    Provenance: this is **not** one of the survey's Table 1 techniques. It is the
    incremental Feline of the author's thesis (Algs. 6-10, Sec. 4.1) —
    R. R. Veloso, *Consultas de alcancabilidade em grafos muito grandes*.
    The static FELINE it extends is Veloso, Cerf, Meira Jr. & Zaki, EDBT 2014.

    Examples
    --------
    >>> import numpy as np
    >>> from pyreachability import Graph
    >>> from pyreachability.dynamic import FelinePK
    >>> g = Graph.from_edges(np.array([0, 1], np.int32),
    ...                      np.array([1, 2], np.int32), num_nodes=3)
    >>> idx = FelinePK(); idx.build(g)
    >>> idx.query(0, 2)
    True
    >>> idx.remove_edge(1, 2)
    >>> idx.query(0, 2)
    False
    """

    name = "feline-pk"
    supports = frozenset({EDGE_INSERT, EDGE_DELETE, VERTEX_INSERT, VERTEX_DELETE})

    def __init__(self):
        self._core = _FelinePKCore()
        self._built = False

    def build(self, graph) -> None:
        self._core.build(graph)
        self._built = True

    def insert_edge(self, u: int, v: int) -> None:
        self._core.insert_edge(int(u), int(v))

    def remove_edge(self, u: int, v: int) -> None:
        self._core.remove_edge(int(u), int(v))

    def insert_vertex(self, v: int) -> None:
        self._core.insert_vertex(int(v))

    def remove_vertex(self, v: int) -> None:
        self._core.remove_vertex(int(v))

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
        """Estimated resident size of the maintained index, in bytes.

        An estimate, not a measurement: it sums the hashmaps' payloads and bucket
        arrays, and cannot see the allocator's overhead. The static half's figures
        are exact array sizes, so do not compare the two as if they were the same
        measurement.
        """
        return self._core.index_size_bytes()
