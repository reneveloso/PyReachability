# =============================================================================
# HOW TO FILL IN (student) — DL (Distribution Labeling)
# Paper: docs/DL.pdf — open at: page 7, "Figure 2" (running example of Cov).
#  1. edges/num_nodes: the example uses the SAME G0 as Figure 1a (p. 5) —
#     copy them from the filled hl.py once its transcription is confirmed.
#  2. queries: facts highlighted in the text (Example 5.1: 7 -> 13;
#     TC(13) subset of TC(7)).
#  (labels=None: Figure 2 shows Cov sets, not a Lin/Lout table; also DL==PLL
#   in the core, with labels in landmark-rank space.)
#  Validate:  pytest tests/paper_examples/test_runner.py -k dl -v
#  If it fails with "transcription error", the error is in YOUR transcription
#  (graph or labels), not in the library — re-check the figure.
#  Portuguese guide: README_pt.md in this folder.
# =============================================================================
from _schema import PaperExample

EXAMPLE = PaperExample(
    method="dl",
    source="Jin & Wang, PVLDB 2013 — Simple, Fast, and Scalable Reachability Oracle",
    figure="Figure 2, p. 1984",
    doi="10.14778/2556549.2556578",
    num_nodes=None,                       # <- STUDENT
    edges=[],                             # <- STUDENT (verbatim from the figure)
    queries=[],                           # <- STUDENT (pairs highlighted in the text)
    labels=None,
)
