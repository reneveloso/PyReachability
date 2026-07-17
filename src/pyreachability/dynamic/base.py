"""The contract for indexes that are maintained under graph updates."""
from ..base import ReachabilityIndex

# --- capability vocabulary -------------------------------------------------
# Two kinds of string live here and must not be mixed:
#   abilities    — things the index can do
#   preconditions — things the CALLER must guarantee
EDGE_INSERT = "edge_insert"
EDGE_DELETE = "edge_delete"
VERTEX_INSERT = "vertex_insert"
VERTEX_DELETE = "vertex_delete"
EDGE_INSERT_BATCH = "edge_insert_batch"   # ability: has a real batch algorithm
ACYCLIC_INSERT_ONLY = "acyclic_insert_only"   # precondition (U2-hop's, if it lands)


class UnsupportedOperation(NotImplementedError):
    """Raised when a method is asked for an update it does not support."""


class DynamicReachabilityIndex(ReachabilityIndex):
    """A reachability index seeded from a graph and then maintained under updates.

    Capabilities are **data, not types**: a method declares what it supports in
    ``supports``, and consumers read it. There is deliberately no
    Incremental/FullyDynamic class hierarchy — the published methods do not form
    that lattice (U2-hop has vertex deletion but only acyclic edge insertion;
    DBL is insertion-only), so a hierarchy would have to lie about some of them.
    """

    supports: frozenset = frozenset()

    def insert_edge(self, u: int, v: int) -> None:
        raise UnsupportedOperation(f"{type(self).__name__} does not support edge insertion")

    def remove_edge(self, u: int, v: int) -> None:
        raise UnsupportedOperation(f"{type(self).__name__} does not support edge deletion")

    def insert_vertex(self, v: int) -> None:
        raise UnsupportedOperation(f"{type(self).__name__} does not support vertex insertion")

    def remove_vertex(self, v: int) -> None:
        raise UnsupportedOperation(f"{type(self).__name__} does not support vertex deletion")

    def insert_edges(self, pairs) -> None:
        """Insert many edges. Defaults to a loop.

        Every dynamic index therefore accepts batches; ``EDGE_INSERT_BATCH`` means
        "I have a real batch algorithm, better than this loop" — not "I accept
        batches". Feline-PK is exactly the loop today: batch insertion is its
        declared future work.
        """
        for u, v in pairs:
            self.insert_edge(u, v)
