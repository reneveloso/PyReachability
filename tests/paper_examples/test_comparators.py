import pytest
from _schema import PaperExample, LabelCheck
from _comparators import cross_check_two_hop, compare


def _example(labels_expected, edges=((0, 1), (1, 2))):
    return PaperExample(
        method="hl", source="selftest", figure="-", doi="-",
        num_nodes=3, edges=list(edges),
        labels=LabelCheck(kind="two_hop", expected=labels_expected),
    )


GOOD = {  # a valid 2-hop labeling of the path 0->1->2 (each vertex records itself)
    0: {"Lin": {0}, "Lout": {0, 1, 2}},
    1: {"Lin": {1}, "Lout": {1, 2}},
    2: {"Lin": {2}, "Lout": {2}},
}


def test_cross_check_accepts_consistent_transcription():
    cross_check_two_hop(_example(GOOD))     # no raise


def test_cross_check_flags_transcription_error():
    bad = {**GOOD, 2: {"Lin": {2}, "Lout": {0, 2}}}   # labels claim 2 -> 0
    with pytest.raises(AssertionError, match="transcription error"):
        cross_check_two_hop(_example(bad))


def test_compare_exact_matches_built_labels():
    # end-to-end against the real HL implementation on the same path graph
    import numpy as np
    from pyreachability import Graph, catalog
    ex = _example(GOOD)
    src = np.array([e[0] for e in ex.edges], np.int32)
    dst = np.array([e[1] for e in ex.edges], np.int32)
    idx = catalog.get("hl")(); idx.build(Graph.from_edges(src, dst, num_nodes=3))
    built = idx.two_hop_labels()
    # exact equality may legitimately fail if HL labels differ from GOOD while
    # still correct; this test asserts the INVARIANT path instead:
    ex.labels.mode = "invariant"
    compare(ex, built)                       # no raise
