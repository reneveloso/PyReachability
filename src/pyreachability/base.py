import abc
import numpy as np


class ReachabilityIndex(abc.ABC):
    """Common contract for every reachability method in the catalog."""

    name: str = ""

    @abc.abstractmethod
    def build(self, graph) -> None:
        """Build the index over a Graph (runs SCC condensation as needed)."""

    @abc.abstractmethod
    def query(self, u: int, v: int) -> bool:
        """Return True iff u reaches v (reflexive: query(u, u) is True)."""

    @abc.abstractmethod
    def query_batch(self, pairs) -> np.ndarray:
        """Vectorized query. pairs: (M, 2) int array -> (M,) bool array."""

    @property
    @abc.abstractmethod
    def index_size_bytes(self) -> int:
        """Resident size of the built index, in bytes (for benchmarking)."""
