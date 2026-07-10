# =============================================================================
# HOW TO FILL IN (student) — Dual Labeling
# Paper: docs/Dual_Labeling_Answering_Graph_Reachability_Queries_in_Constant_Time.pdf — open at: page 4, "Figure 1" (input graph) and "Figure 2" (spanning tree with interval labels).
#  1. edges: transcribe the graph of Figure 1.
#  2. num_nodes: highest id + 1.
#  3. queries: pairs used in the text for tree-labels vs non-tree links.
#  (labels=None for now: the index is intervals + a transitive link table —
#   its own comparator kind in the future.)
#  Validate:  pytest tests/paper_examples/test_runner.py -k dual -v
#  If it fails with "transcription error", the error is in YOUR transcription
#  (graph or labels), not in the library — re-check the figure.
#  Portuguese guide: README_pt.md in this folder.
# =============================================================================
from _schema import PaperExample

EXAMPLE = PaperExample(
    method="dual",
    source="Wang, He, Yang, Yu, Yu, ICDE 2006 — Dual Labeling",
    figure="Figures 1–2, p. 4",
    doi="10.1109/ICDE.2006.53",
    num_nodes=None,                       # <- STUDENT
    edges=[],                             # <- STUDENT (verbatim from the figure)
    queries=[],                           # <- STUDENT (pairs highlighted in the text)
    labels=None,
)
