import numpy as np
import pytest
from hypothesis import given, settings, strategies as st

from pyreachability import Graph, catalog
from pyreachability._oracle import reachable_set
from pyreachability.dynamic import FelinePK
from pyreachability.dynamic import base as dyn_base


def _oracle(n, edges, u, v):
    return v in reachable_set(n, edges)[u]


def test_seeds_from_a_static_graph_then_evolves():
    g = Graph.from_edges(np.array([0, 1], np.int32), np.array([1, 2], np.int32), num_nodes=3)
    idx = FelinePK()
    idx.build(g)
    assert idx.query(0, 2)
    idx.remove_edge(1, 2)
    assert not idx.query(0, 2)
    idx.insert_edge(0, 2)
    assert idx.query(0, 2)


def test_declares_all_four_abilities():
    assert FelinePK.supports == frozenset({
        dyn_base.EDGE_INSERT, dyn_base.EDGE_DELETE,
        dyn_base.VERTEX_INSERT, dyn_base.VERTEX_DELETE,
    })
    # Batch insertion is Feline-PK's declared future work: it IS the loop today.
    assert dyn_base.EDGE_INSERT_BATCH not in FelinePK.supports


def test_is_registered_as_dynamic():
    assert "feline-pk" in catalog.methods(kind="dynamic")
    assert "feline-pk" not in catalog.methods(kind="static")


def test_query_before_build_raises():
    idx = FelinePK()
    with pytest.raises(RuntimeError):
        idx.query(0, 1)
    with pytest.raises(RuntimeError):
        idx.query_batch(np.array([[0, 1]], np.int32))


def test_scc_fold_happens_during_build():
    """build() seeds edge-by-edge into the same incremental insert_edge as
    runtime updates use, so a cycle present at seed time must fold during
    build() itself -- there is no separate one-shot condensation pass here
    (unlike the static half). Seed a 3-cycle with a tail on each end.

    Edge order inside build() matters here, not just for style: it iterates
    vertices in ascending id and inserts each one's out-edges in turn, so an
    edge whose source has a *smaller* id than the cycle-closing edge's source
    lands in the DAG before the fold happens -- landing 0->1 and 2->4 before
    the closing edge 3->1 forces the fold's own I/O predecessor/successor
    rewiring to run with both sets non-empty. Get this backwards (e.g. route
    the tail through vertex 3, whose out-edges are processed last) and the
    tail edges get added as fresh, ordinary edges *after* the fold instead of
    exercising the fold's I/O rewiring at all -- silently making this test
    pass on a build that drops that rewiring. Confirmed by mutation: dropping
    the I-side rewiring line in fold_cycle breaks 0->1 in this exact layout
    while leaving every other assertion in this file green."""
    # 0 -> {1,2,3} (a 3-cycle, closed by the last edge 3->1) -> 4
    g = Graph.from_edges(
        np.array([0, 1, 2, 2, 3], np.int32),
        np.array([1, 2, 3, 4, 1], np.int32),
        num_nodes=5,
    )
    idx = FelinePK()
    idx.build(g)
    cycle = [1, 2, 3]
    for a in cycle:
        for b in cycle:
            assert idx.query(a, b), f"{a}->{b} should hold: same SCC"
    for a in cycle:
        assert idx.query(0, a)
        assert not idx.query(a, 0)
        assert idx.query(a, 4)
        assert not idx.query(4, a)
    assert not idx.query(4, 0)


def test_remove_edge_splits_a_component_all_four_directions():
    """Two 2-cycles {0,1} and {2,3}, joined into one 4-cycle by 1->2 and 3->0
    so build() folds all four into a single SCC. Vertex 4 has a direct edge
    into the component (4->0) and vertex 5 receives a direct edge out of it
    (3->5) -- neither 4 nor 5 is itself folded into the SCC, so after the
    split their DAG links can only be restored by split_component's re-insert
    loop scanning the *other* endpoint (4->0 needs pred(0), 3->5 needs
    succ(3); an edge fully internal to the split component, like the
    surviving bridge 3->0, would be reinstated by either loop alone and so
    would not tell the two apart).

    Removing 1->2 breaks only the forward bridge: {0,1} and {2,3} stay
    individually cyclic, and the surviving 3->0 bridge makes {2,3} -> {0,1}
    reachable but not the reverse. Checks all four directions: within-A,
    within-B, B->A, A->B, plus the two external edges crossing the split."""
    g = Graph.from_edges(
        np.array([0, 1, 1, 2, 3, 3, 4, 3], np.int32),
        np.array([1, 0, 2, 3, 2, 0, 0, 5], np.int32),
        num_nodes=6,
    )
    idx = FelinePK()
    idx.build(g)
    # Before removal: one SCC of all four, 4 reaches everything, everything reaches 5.
    for a in range(4):
        for b in range(4):
            assert idx.query(a, b), f"pre-split {a}->{b} should hold: one SCC"
    for a in range(4):
        assert idx.query(4, a)
        assert idx.query(a, 5)
    assert idx.query(4, 5)

    idx.remove_edge(1, 2)

    # within {0, 1}: untouched 2-cycle
    assert idx.query(0, 1)
    assert idx.query(1, 0)
    # within {2, 3}: untouched 2-cycle
    assert idx.query(2, 3)
    assert idx.query(3, 2)
    # {2, 3} -> {0, 1}: surviving bridge 3->0
    assert idx.query(2, 0)
    assert idx.query(2, 1)
    assert idx.query(3, 0)
    assert idx.query(3, 1)
    # {0, 1} -> {2, 3}: bridge removed, no path back
    assert not idx.query(0, 2)
    assert not idx.query(0, 3)
    assert not idx.query(1, 2)
    assert not idx.query(1, 3)
    # external edge INTO the split component (4->0): direct edge, must survive
    # regardless of the bridge -- exercises split_component's pred(w) re-insert.
    assert idx.query(4, 0)
    assert idx.query(4, 1)
    assert not idx.query(4, 2)   # only reachable by crossing the now-removed bridge
    assert not idx.query(4, 3)
    # external edge OUT of the split component (3->5): exercises succ(w) re-insert.
    assert idx.query(2, 5)
    assert idx.query(3, 5)
    assert not idx.query(0, 5)   # A can no longer reach B, so cannot reach 5 either
    assert not idx.query(1, 5)


def test_query_batch_matches_query_loop():
    g = Graph.from_edges(np.array([0, 1, 3], np.int32), np.array([1, 2, 4], np.int32), num_nodes=5)
    idx = FelinePK()
    idx.build(g)
    idx.remove_edge(1, 2)
    idx.insert_edge(2, 3)
    pairs = [(a, b) for a in range(5) for b in range(5)]
    batch = idx.query_batch(np.array(pairs, dtype=np.int32))
    loop = [idx.query(a, b) for a, b in pairs]
    assert list(batch) == loop
    assert batch.dtype == np.bool_


def test_query_batch_has_no_upper_bound_and_tolerates_bootstrapped_vertices():
    """query_batch deliberately has no upper-bound check: Feline-PK has no
    fixed vertex count, and insert_edge bootstraps vertices past build()'s
    original n. An id the index has never seen at all must be tolerated too
    (reachable() returns False), matching query()'s behaviour -- not raise."""
    g = Graph.from_edges(np.array([0], np.int32), np.array([1], np.int32), num_nodes=2)
    idx = FelinePK()
    idx.build(g)
    idx.insert_edge(1, 50)  # bootstraps vertex 50, never part of build()
    assert idx.query(0, 50) is True
    assert idx.query(0, 999) is False   # 999 was never created anywhere

    pairs = np.array([[0, 50], [50, 0], [0, 999]], dtype=np.int32)
    batch = idx.query_batch(pairs)
    assert list(batch) == [idx.query(0, 50), idx.query(50, 0), idx.query(0, 999)]
    assert list(batch) == [True, False, False]


def test_negative_vertex_id_is_rejected():
    g = Graph.from_edges(np.array([0], np.int32), np.array([1], np.int32), num_nodes=2)
    idx = FelinePK()
    idx.build(g)
    with pytest.raises(IndexError):
        idx.query(-1, 0)
    with pytest.raises(IndexError):
        idx.insert_edge(-1, 0)
    with pytest.raises(IndexError):
        idx.remove_edge(0, -1)
    with pytest.raises(IndexError):
        idx.insert_vertex(-1)
    with pytest.raises(IndexError):
        idx.remove_vertex(-1)
    with pytest.raises(IndexError):
        idx.query_batch(np.array([[0, -1]], dtype=np.int32))


@settings(max_examples=50, deadline=None)
@given(
    n=st.integers(min_value=2, max_value=6),
    ops=st.lists(
        st.tuples(st.booleans(), st.integers(0, 5), st.integers(0, 5)),
        min_size=1, max_size=25,
    ),
)
def test_update_sequences_agree_with_the_oracle(n, ops):
    """The oracle with a time axis: re-check every pair after every update."""
    idx = FelinePK()
    idx.build(Graph.from_edges(np.empty(0, np.int32), np.empty(0, np.int32), num_nodes=n))
    edges = []
    for inserting, u, v in ops:
        if u >= n or v >= n or u == v:
            continue
        if inserting:
            idx.insert_edge(u, v)
            if (u, v) not in edges:
                edges.append((u, v))
        else:
            idx.remove_edge(u, v)
            edges = [e for e in edges if e != (u, v)]
        for a in range(n):
            for b in range(n):
                assert idx.query(a, b) == _oracle(n, edges, a, b), (
                    f"after {'insert' if inserting else 'remove'} {u}->{v}: {a}->{b}"
                )


@settings(max_examples=30, deadline=None)
@given(
    n=st.integers(min_value=2, max_value=6),
    ops=st.lists(
        st.tuples(st.booleans(), st.integers(0, 5), st.integers(0, 5)),
        min_size=1, max_size=15,
    ),
)
def test_query_batch_agrees_with_query_through_updates(n, ops):
    """query_batch's own marshalling (dtype casts, reshape, min-check) is a
    second crossing of the Python/C++ boundary that scalar query() does not
    exercise -- check it stays in lockstep with query() through the same
    update sequences the time-axis oracle uses."""
    idx = FelinePK()
    idx.build(Graph.from_edges(np.empty(0, np.int32), np.empty(0, np.int32), num_nodes=n))
    for inserting, u, v in ops:
        if u >= n or v >= n or u == v:
            continue
        if inserting:
            idx.insert_edge(u, v)
        else:
            idx.remove_edge(u, v)
    pairs = [(a, b) for a in range(n) for b in range(n)]
    batch = idx.query_batch(np.array(pairs, dtype=np.int32))
    loop = [idx.query(a, b) for a, b in pairs]
    assert list(batch) == loop
