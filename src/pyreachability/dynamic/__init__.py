"""Dynamic reachability indexes — seeded from a graph, then maintained under updates."""
from .base import (DynamicReachabilityIndex, UnsupportedOperation,
                   EDGE_INSERT, EDGE_DELETE, VERTEX_INSERT, VERTEX_DELETE,
                   EDGE_INSERT_BATCH, ACYCLIC_INSERT_ONLY)

__all__ = ["DynamicReachabilityIndex", "UnsupportedOperation",
           "EDGE_INSERT", "EDGE_DELETE", "VERTEX_INSERT", "VERTEX_DELETE",
           "EDGE_INSERT_BATCH", "ACYCLIC_INSERT_ONLY"]
