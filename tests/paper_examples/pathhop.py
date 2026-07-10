# =============================================================================
# HOW TO FILL IN (student) — Path-Hop
# Paper: docs/path-hop.pdf — open at: pages 3–6, "Figures 1–4" (chain decomposition, RTC, hop cover, path-hop).
#  1. edges: transcribe the base graph of Figures 1–2.
#  2. num_nodes: highest id + 1.
#  3. queries: pairs the text resolves via tree + hops.
#  (labels=None for now.)
#  Validate:  pytest tests/paper_examples/test_runner.py -k pathhop -v
#  If it fails with "transcription error", the error is in YOUR transcription
#  (graph or labels), not in the library — re-check the figure.
#  Portuguese guide: README_pt.md in this folder.
# =============================================================================
from _schema import PaperExample

EXAMPLE = PaperExample(
    method="pathhop",
    source="Cai & Poon, CIKM 2010 — Path-Hop",
    figure="Figures 1–4, pp. 3–6",
    doi="10.1145/1871437.1871457",
    num_nodes=None,                       # <- STUDENT
    edges=[],                             # <- STUDENT (verbatim from the figure)
    queries=[],                           # <- STUDENT (pairs highlighted in the text)
    labels=None,
)
