# =============================================================================
# HOW TO FILL IN (student) — PReaCH
# Paper: docs/preach.pdf — open at: page 6, "Figure 1" (example RCH) and page 7, "Figure 2" (topological levels).
#  1. edges: transcribe the example graph (Figure 1/2).
#  2. num_nodes: highest id + 1.
#  3. queries: pairs the text decides via levels/intervals.
#  (labels=None for now.)
#  Validate:  pytest tests/paper_examples/test_runner.py -k preach -v
#  If it fails with "transcription error", the error is in YOUR transcription
#  (graph or labels), not in the library — re-check the figure.
#  Portuguese guide: README_pt.md in this folder.
# =============================================================================
from _schema import PaperExample

EXAMPLE = PaperExample(
    method="preach",
    source="Merz & Sanders, ESA 2014 — PReaCH",
    figure="Figures 1–2, pp. 6–7",
    doi="10.1007/978-3-662-44777-2_58",
    num_nodes=None,                       # <- STUDENT
    edges=[],                             # <- STUDENT (verbatim from the figure)
    queries=[],                           # <- STUDENT (pairs highlighted in the text)
    labels=None,
)
