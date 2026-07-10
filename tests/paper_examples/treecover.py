# =============================================================================
# HOW TO FILL IN (student) — Tree Cover (Agrawal)
# Paper: docs/agrawal.pdf — open at: page 3, "Figure 3.3" (two different tree-covers for the same graph).
#  1. edges: transcribe the graph of Figure 3.3.
#  2. num_nodes: highest id + 1 (map letters -> integers if needed; note it).
#  3. queries: pairs the text uses when explaining interval compression.
#  (labels=None for now: an "intervals" comparator does not exist yet — see README.)
#  Validate:  pytest tests/paper_examples/test_runner.py -k treecover -v
#  If it fails with "transcription error", the error is in YOUR transcription
#  (graph or labels), not in the library — re-check the figure.
#  Portuguese guide: README_pt.md in this folder.
# =============================================================================
from _schema import PaperExample

EXAMPLE = PaperExample(
    method="treecover",
    source="Agrawal, Borgida, Jagadish, SIGMOD 1989 — Efficient Management of Transitive Relationships",
    figure="Figure 3.3, p. 3",
    doi="10.1145/67544.66950",
    num_nodes=None,                       # <- STUDENT
    edges=[],                             # <- STUDENT (verbatim from the figure)
    queries=[],                           # <- STUDENT (pairs highlighted in the text)
    labels=None,
)
