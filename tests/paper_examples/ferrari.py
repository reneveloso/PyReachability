# =============================================================================
# HOW TO FILL IN (student) — Ferrari
# Paper: docs/ferrari.pdf — open at: "Fig. 1"–"Fig. 2" (example graph with exact/approximate intervals; captions extract on p. 10 in this PDF version).
#  1. edges: transcribe the graph of Fig. 1.
#  2. num_nodes: highest id + 1.
#  3. queries: pairs the text decides via exact vs approximate intervals.
#  (labels=None for now: "intervals" comparator in the future.)
#  Validate:  pytest tests/paper_examples/test_runner.py -k ferrari -v
#  If it fails with "transcription error", the error is in YOUR transcription
#  (graph or labels), not in the library — re-check the figure.
#  Portuguese guide: README_pt.md in this folder.
# =============================================================================
from _schema import PaperExample

EXAMPLE = PaperExample(
    method="ferrari",
    source="Seufert, Anand, Bedathur, Weikum, ICDE 2013 — FERRARI",
    figure="Figs. 1–2 (see p. 10 in this version)",
    doi="10.1109/ICDE.2013.6544893",
    num_nodes=None,                       # <- STUDENT
    edges=[],                             # <- STUDENT (verbatim from the figure)
    queries=[],                           # <- STUDENT (pairs highlighted in the text)
    labels=None,
)
