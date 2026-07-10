# =============================================================================
# HOW TO FILL IN (student) — O'Reach
# Paper: docs/oreach.pdf — open at: page 7, "Figure 1" (extended topological sorting example).
#  1. edges: transcribe the graph of Figure 1.
#  2. num_nodes: highest id + 1.
#  3. queries: pairs the text's O(1) observations decide.
#  (labels=None: the observations use heuristically chosen supportive
#   vertices — not reproducible verbatim.)
#  Validate:  pytest tests/paper_examples/test_runner.py -k oreach -v
#  If it fails with "transcription error", the error is in YOUR transcription
#  (graph or labels), not in the library — re-check the figure.
#  Portuguese guide: README_pt.md in this folder.
# =============================================================================
from _schema import PaperExample

EXAMPLE = PaperExample(
    method="oreach",
    source="Hanauer, Schulz, Trummer, ACM JEA 2022 — O'Reach",
    figure="Figure 1, p. 7",
    doi="10.1145/3556540",
    num_nodes=None,                       # <- STUDENT
    edges=[],                             # <- STUDENT (verbatim from the figure)
    queries=[],                           # <- STUDENT (pairs highlighted in the text)
    labels=None,
)
