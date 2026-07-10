# =============================================================================
# HOW TO FILL IN (student) — 3-Hop
# Paper: docs/3-hop.pdf — open at: page 4, "Figure 1" (a simple example for 3-hop and 2-hop).
#  1. edges: transcribe the graph of Figure 1.
#  2. num_nodes: highest id + 1.
#  3. queries: pairs resolved via highway chains in the text.
#  (labels=None for now.)
#  Validate:  pytest tests/paper_examples/test_runner.py -k threehop -v
#  If it fails with "transcription error", the error is in YOUR transcription
#  (graph or labels), not in the library — re-check the figure.
#  Portuguese guide: README_pt.md in this folder.
# =============================================================================
from _schema import PaperExample

EXAMPLE = PaperExample(
    method="threehop",
    source="Jin, Xiang, Ruan, Fuhry, SIGMOD 2009 — 3-HOP",
    figure="Figure 1, p. 4",
    doi="10.1145/1559845.1559930",
    num_nodes=None,                       # <- STUDENT
    edges=[],                             # <- STUDENT (verbatim from the figure)
    queries=[],                           # <- STUDENT (pairs highlighted in the text)
    labels=None,
)
