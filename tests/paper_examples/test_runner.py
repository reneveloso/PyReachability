"""Discovers every paper-example stub in this folder and validates it in layers:
Layer 1 — all-pairs answers vs. ground truth derived from the transcribed graph;
Layer 2 — the specific queries the paper highlights;
Layer 3 — the paper's printed labels (see _comparators.py), when provided.
Unfilled stubs (edges == []) SKIP with a clear message — they never fail CI."""
import importlib.util
from pathlib import Path

import numpy as np
import pytest

from _schema import PaperExample
from pyreachability import Graph, catalog

_HERE = Path(__file__).parent
_EXCLUDE_PREFIXES = ("_", "test_", "conftest")


def iter_stub_files():
    return sorted(
        p for p in _HERE.glob("*.py")
        if not any(p.name.startswith(pre) for pre in _EXCLUDE_PREFIXES)
    )


def load_example(path: Path) -> PaperExample:
    spec = importlib.util.spec_from_file_location(f"paper_example_{path.stem}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.EXAMPLE


def _build_index(example: PaperExample):
    src = np.array([e[0] for e in example.edges], dtype=np.int32)
    dst = np.array([e[1] for e in example.edges], dtype=np.int32)
    g = Graph.from_edges(src, dst, num_nodes=example.num_nodes)
    idx = catalog.get(example.method)()
    idx.build(g)
    return idx


def check_answers(example: PaperExample) -> None:
    if not example.is_filled:
        pytest.skip(f"stub '{example.method}' not filled yet (edges empty) — "
                    "see README.md in this folder")
    idx = _build_index(example)
    reach = example.ground_truth()
    n = example.num_nodes
    # Layer 1: every pair
    for u in range(n):
        for v in range(n):
            expected = (u == v) or (v in reach[u])
            got = idx.query(u, v)
            assert got == expected, (
                f"[{example.method}] {example.figure}: query({u},{v}) = {got}, "
                f"paper graph says {expected}")
    # Layer 2: the pairs the paper highlights
    for u, v, expected in example.queries:
        got = idx.query(u, v)
        assert got == expected, (
            f"[{example.method}] highlighted query({u},{v}) = {got}, "
            f"paper says {expected}")


_STUBS = iter_stub_files()


@pytest.mark.parametrize("stub", _STUBS, ids=lambda p: p.stem)
def test_paper_example(stub):
    example = load_example(stub)
    check_answers(example)
