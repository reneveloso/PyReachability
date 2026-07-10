# =============================================================================
# HOW TO FILL IN (student) — IP (Independent Permutation)
# Paper: docs/ip.pdf — open at: "Figure 1(a)" (graph G) and page 7, "Figure 2" (Level Labels for G).
#  1. edges: transcribe graph G of Figure 1(a).
#  2. num_nodes: highest id + 1.
#  3. queries: pairs discussed in the text.
#  (labels=None: the k-min-wise labels come from a RANDOM permutation — not
#   reproducible verbatim; the Level Labels of Figure 2 could become their own
#   comparator kind in the future.)
#  Validate:  pytest tests/paper_examples/test_runner.py -k ip -v
#  If it fails with "transcription error", the error is in YOUR transcription
#  (graph or labels), not in the library — re-check the figure.
#  Portuguese guide: README_pt.md in this folder.
# =============================================================================
from _schema import PaperExample

EXAMPLE = PaperExample(
    method="ip",
    source="Wei, Yu, Lu, Jin, PVLDB 2014 — Reachability Querying: An Independent Permutation Labeling Approach",
    figure="Figure 1(a) + Figure 2, p. 7",
    doi="10.14778/2732977.2732992",
    num_nodes=None,                       # <- STUDENT
    edges=[],                             # <- STUDENT (verbatim from the figure)
    queries=[],                           # <- STUDENT (pairs highlighted in the text)
    labels=None,
)
