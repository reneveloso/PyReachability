"""Label comparators, one per LabelCheck.kind. Every comparator first runs the
transcription cross-check: the reachability implied by the paper's labels must
equal the reachability derived from the transcribed edges. A mismatch means the
student mis-copied the figure — the error is in the data file, not the library."""
from __future__ import annotations

from _schema import PaperExample


def _pairs_from_two_hop(labels: dict, verts) -> set:
    """Ordered pairs (u, v), u != v, decided reachable by Lout(u) ∩ Lin(v),
    restricted to `verts` — papers often print only part of the label table."""
    out = set()
    for u in verts:
        for v in verts:
            if u != v and (labels[u]["Lout"] & labels[v]["Lin"]):
                out.add((u, v))
    return out


def cross_check_two_hop(example: PaperExample) -> None:
    verts = sorted(example.labels.expected.keys())
    reach = example.ground_truth()
    from_graph = {(u, v) for u in verts for v in verts if u != v and v in reach[u]}
    from_labels = _pairs_from_two_hop(example.labels.expected, verts)
    assert from_graph == from_labels, (
        f"[{example.method}] {example.figure}: transcription error (graph or "
        f"labels mis-copied from the paper). Reachability from the transcribed "
        f"edges and from the transcribed labels disagree on: "
        f"{sorted(from_graph ^ from_labels)}")


def _compare_two_hop(example: PaperExample, built: dict) -> None:
    cross_check_two_hop(example)
    verts = sorted(example.labels.expected.keys())
    if example.labels.mode == "exact":
        got = {v: built[v] for v in verts}
        assert got == example.labels.expected, (
            f"[{example.method}] built Lin/Lout differ from the paper's "
            f"{example.figure}")
    else:  # invariant: the built labels must induce the same reachability
        assert _pairs_from_two_hop(built, verts) == _pairs_from_two_hop(
            example.labels.expected, verts), (
            f"[{example.method}] built labels induce a different reachability "
            f"than the paper's {example.figure}")


COMPARATORS = {"two_hop": _compare_two_hop}


def compare(example: PaperExample, built: dict) -> None:
    kind = example.labels.kind
    assert kind in COMPARATORS, (
        f"no comparator for kind='{kind}' yet — add one to _comparators.py "
        f"(see the spec's 'When a predefined format doesn't fit' section)")
    COMPARATORS[kind](example, built)
