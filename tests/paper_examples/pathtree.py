# =============================================================================
# HOW TO FILL IN (student) — Path-Tree
# Paper: docs/path-tree.pdf — open at: pages 13–15, "Fig. 5" and "Fig. 6" (complete labeling for the path-tree).
#  1. edges: transcribe the graph of the examples (Fig. 4a/5).
#  2. num_nodes: highest id + 1.
#  3. queries: pairs the text resolves with the 3-tuple labels.
#  (labels=None for now: 3-tuple labels would get their own comparator kind.)
#  Validate:  pytest tests/paper_examples/test_runner.py -k pathtree -v
#  If it fails with "transcription error", the error is in YOUR transcription
#  (graph or labels), not in the library — re-check the figure.
#  Portuguese guide: README_pt.md in this folder.
# =============================================================================
from _schema import PaperExample

EXAMPLE = PaperExample(
    method="pathtree",
    source="Jin, Ruan, Xiang, Wang, ACM TODS 2011 — Path-Tree",
    figure="Figs. 5–6, pp. 13–15",
    doi="10.1145/1929934.1929941",
    num_nodes=None,                       # <- STUDENT
    edges=[],                             # <- STUDENT (verbatim from the figure)
    queries=[],                           # <- STUDENT (pairs highlighted in the text)
    labels=None,
)
