"""Worked-example validation against hand-written ground truth.

The property-based suites (``test_<method>.py``) already check every method against a BFS/DFS oracle
on hundreds of random graphs. This module complements them with small, **hand-verifiable** DAGs whose
complete reachability is written out explicitly below — *independent* ground truth, not derived from
any other index. Every catalogued method must reproduce it on **all** vertex pairs.

Each example is annotated with the paper concept it exercises (chains, tree-cover intervals, the
diamond/poset that 2-hop & dual-labeling target, non-tree "hop" edges, multiple components, and the
SCC condensation that every method relies on). This gives a single, reviewer-checkable place that
shows the library answers the textbook reachability scenarios from the source publications exactly.

NOTE on verbatim paper figures: the verbatim transcriptions now live in
``tests/paper_examples/`` (one data file per method, filled from each paper's
running-example figure, with a transcription cross-check). This module keeps the
hand-built structural DAGs as a fast, always-on complement.
"""
import numpy as np
import pytest

from pyreachability import Graph, catalog


# Each example: (name, num_nodes, edges, reach) where reach[u] is the exact set of v != u with u ->* v.
# `reach` is written by hand (ground truth); cyclic examples encode mutual SCC reachability.
def _chain():
    # Linear chain — the "highway" structure behind Chain Cover / 3-Hop / Path-Tree.
    edges = [(0, 1), (1, 2), (2, 3), (3, 4)]
    reach = {0: {1, 2, 3, 4}, 1: {2, 3, 4}, 2: {3, 4}, 3: {4}, 4: set()}
    return ("chain", 5, edges, reach)


def _out_tree():
    # Rooted out-tree — the interval-containment structure behind Tree Cover (Agrawal).
    edges = [(0, 1), (0, 2), (1, 3), (1, 4), (2, 5), (2, 6)]
    reach = {0: {1, 2, 3, 4, 5, 6}, 1: {3, 4}, 2: {5, 6}, 3: set(), 4: set(), 5: set(), 6: set()}
    return ("out_tree", 7, edges, reach)


def _diamond():
    # Diamond / small poset — pairs covered by a single 2-hop center; dual-labeling tree + 1 link.
    edges = [(0, 1), (0, 2), (1, 3), (2, 3), (3, 4)]
    reach = {0: {1, 2, 3, 4}, 1: {3, 4}, 2: {3, 4}, 3: {4}, 4: set()}
    return ("diamond", 5, edges, reach)


def _cross_dag():
    # Interleaved DAG with non-tree ("hop") edges — GRIPP / Dual / Tree+SSPI residual edges.
    edges = [(0, 1), (0, 2), (1, 3), (2, 4), (1, 4), (2, 3), (3, 5), (4, 5)]
    reach = {
        0: {1, 2, 3, 4, 5},
        1: {3, 4, 5},
        2: {3, 4, 5},
        3: {5},
        4: {5},
        5: set(),
    }
    return ("cross_dag", 6, edges, reach)


def _two_components():
    # Two disjoint components + an isolated vertex — WCC handling (O'Reach B2), condensation.
    edges = [(0, 1), (1, 2), (3, 4)]
    reach = {0: {1, 2}, 1: {2}, 2: set(), 3: {4}, 4: set(), 5: set()}
    return ("two_components", 6, edges, reach)


def _scc_cycle():
    # A 3-cycle (one SCC) feeding a tail — exercises the SCC condensation every method applies.
    edges = [(0, 1), (1, 2), (2, 0), (2, 3), (3, 4)]
    reach = {
        0: {1, 2, 3, 4},
        1: {0, 2, 3, 4},
        2: {0, 1, 3, 4},
        3: {4},
        4: set(),
    }
    return ("scc_cycle", 5, edges, reach)


def _wide_poset():
    # Bipartite-ish width-3 poset — an antichain of 3 sources over 3 sinks (Dilworth width = 3).
    edges = [(0, 3), (0, 4), (1, 4), (1, 5), (2, 5), (2, 3)]
    reach = {0: {3, 4}, 1: {4, 5}, 2: {3, 5}, 3: set(), 4: set(), 5: set()}
    return ("wide_poset", 6, edges, reach)


EXAMPLES = [
    _chain(), _out_tree(), _diamond(), _cross_dag(),
    _two_components(), _scc_cycle(), _wide_poset(),
]

METHODS = catalog.methods()


def _build(name, n, edges):
    src = np.array([e[0] for e in edges], dtype=np.int32)
    dst = np.array([e[1] for e in edges], dtype=np.int32)
    g = Graph.from_edges(src, dst, num_nodes=n)
    idx = catalog.get(name)()
    idx.build(g)
    return idx


@pytest.mark.parametrize("example", EXAMPLES, ids=lambda e: e[0])
@pytest.mark.parametrize("method", METHODS)
def test_method_matches_hand_truth(method, example):
    ex_name, n, edges, reach = example
    idx = _build(method, n, edges)
    for u in range(n):
        for v in range(n):
            expected = (u == v) or (v in reach[u])
            assert idx.query(u, v) == expected, (
                f"{method} on '{ex_name}': query({u},{v}) = {idx.query(u, v)}, expected {expected}"
            )


def test_all_methods_agree_on_each_example():
    """Cross-method consistency: every method agrees with the hand truth (and thus each other)."""
    for ex_name, n, edges, reach in EXAMPLES:
        for method in METHODS:
            idx = _build(method, n, edges)
            got = {(u, v) for u in range(n) for v in range(n) if idx.query(u, v)}
            want = {(u, v) for u in range(n) for v in range(n) if (u == v or v in reach[u])}
            assert got == want, f"{method} disagrees on '{ex_name}'"


def _max_antichain_size(n, reach):
    """DAG width = size of the largest antichain (set of pairwise-unreachable vertices). Brute force
    over subsets — only used on the small worked examples, an independent witness for Dilworth."""
    comparable = [[False] * n for _ in range(n)]
    for u in range(n):
        for v in reach[u]:
            comparable[u][v] = comparable[v][u] = True
    best = 0
    for mask in range(1 << n):
        verts = [i for i in range(n) if mask & (1 << i)]
        if all(not comparable[a][b] for i, a in enumerate(verts) for b in verts[i + 1:]):
            best = max(best, len(verts))
    return best


@pytest.mark.parametrize("example", EXAMPLES, ids=lambda e: e[0])
def test_optimal_chain_cover_achieves_dilworth_width(example):
    """Chen & Chen's central claim: the decomposition uses the *minimum* number of chains, which by
    Dilworth's theorem equals the DAG's width (the largest antichain). Acyclic examples only."""
    ex_name, n, edges, reach = example
    if ex_name == "scc_cycle":
        pytest.skip("condensation collapses the cycle; width is defined on the DAG")
    width = _max_antichain_size(n, reach)
    idx = _build("optchain", n, edges)
    assert idx.num_chains() == width, f"'{ex_name}': {idx.num_chains()} chains, Dilworth width {width}"
