# =============================================================================
# HOW TO FILL IN (student) — GRIPP
# Paper: docs/gripp.pdf — open at: page 4, "Figure 1" (Graph G and its GRIPP index table).
#  1. edges: transcribe graph G of Figure 1 (left side).
#  2. num_nodes: highest id + 1 (letter vertices -> integers; note the mapping).
#  3. queries: the text evaluates reach(D, r) in Figure 3 — include those pairs.
#  (labels=None for now: the index is the pre/post-order instance table.)
#  Validate:  pytest tests/paper_examples/test_runner.py -k gripp -v
#  If it fails with "transcription error", the error is in YOUR transcription
#  (graph or labels), not in the library — re-check the figure.
#  Portuguese guide: README_pt.md in this folder.
# =============================================================================
from _schema import PaperExample

EXAMPLE = PaperExample(
    method="gripp",
    source="Trißl & Leser, SIGMOD 2007 — Fast and Practical Indexing and Querying of Very Large Graphs",
    figure="Figure 1, p. 4",
    doi="10.1145/1247480.1247573",
    num_nodes=None,                       # <- STUDENT
    edges=[],                             # <- STUDENT (verbatim from the figure)
    queries=[],                           # <- STUDENT (pairs highlighted in the text)
    labels=None,
)
