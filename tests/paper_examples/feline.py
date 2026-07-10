# =============================================================================
# HOW TO FILL IN (student) — FELINE
# Paper: docs/paper_166.pdf — open at: page 4, "Figure 2" (small DAG with coordinates) and "Figure 3".
#  1. edges: transcribe the DAG of Figure 2(A).
#  2. num_nodes: highest vertex id + 1 (if the figure labels vertices with
#     letters, map letters -> integers alphabetically and note the mapping here).
#  3. queries: pairs discussed in the text (dominance regions, Fig. 4 exceptions).
#  (labels=None for now: a "coords_2d" comparator does not exist yet — see README.)
#  Validate:  pytest tests/paper_examples/test_runner.py -k feline -v
#  If it fails with "transcription error", the error is in YOUR transcription
#  (graph or labels), not in the library — re-check the figure.
#  Portuguese guide: README_pt.md in this folder.
# =============================================================================
from _schema import PaperExample

EXAMPLE = PaperExample(
    method="feline",
    source="Veloso, Cerf, Meira Jr., Zaki, EDBT 2014 — Reachability Queries in Very Large Graphs",
    figure="Figures 2–3, p. 4",
    doi="10.5441/002/edbt.2014.46",
    num_nodes=None,                       # <- STUDENT
    edges=[],                             # <- STUDENT (verbatim from the figure)
    queries=[],                           # <- STUDENT (pairs highlighted in the text)
    labels=None,
)
