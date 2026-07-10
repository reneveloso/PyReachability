"""Declarative schema for verbatim paper examples. See README.md in this folder."""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple


def derive_reach(num_nodes: int, edges: List[Tuple[int, int]]) -> Dict[int, Set[int]]:
    """BFS reachability from every vertex. reach[u] contains u itself only when
    u lies on a cycle (matches the query semantics: query(u, u) is always True,
    but reach[] is the *strict* forward set plus cycle self-reach)."""
    adj: List[List[int]] = [[] for _ in range(num_nodes)]
    for u, v in edges:
        adj[u].append(v)
    reach: Dict[int, Set[int]] = {}
    for s in range(num_nodes):
        seen: Set[int] = set()
        dq = deque(adj[s])
        while dq:
            v = dq.popleft()
            if v in seen:
                continue
            seen.add(v)
            dq.extend(adj[v])
        reach[s] = seen
    return reach


@dataclass
class LabelCheck:
    kind: str                 # "two_hop" | ... (open set; one comparator per kind)
    expected: dict            # shape depends on kind (see _comparators.py)
    mode: str = "exact"       # "exact" | "invariant"


@dataclass
class PaperExample:
    method: str               # catalog key, e.g. "hl"
    source: str               # human-readable citation
    figure: str               # e.g. "Figure 1, p. 1982"
    doi: str
    num_nodes: Optional[int]
    edges: List[Tuple[int, int]]
    reach: Optional[Dict[int, Set[int]]] = None   # None => derive from edges
    queries: List[Tuple[int, int, bool]] = field(default_factory=list)
    labels: Optional[LabelCheck] = None

    @property
    def is_filled(self) -> bool:
        return bool(self.edges)

    def ground_truth(self) -> Dict[int, Set[int]]:
        if self.reach is not None:
            return self.reach
        return derive_reach(self.num_nodes, self.edges)
