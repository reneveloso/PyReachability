# =============================================================================
# HOW TO FILL IN (student) — 2-Hop (Cohen et al.)
# Paper: docs/2-hop.pdf — open at: page 5, "Figure 1" (solid = graph edges, dashed = hops).
#  1. edges: transcribe ONLY the solid edges of Figure 1.
#  2. num_nodes: highest id + 1.
#  3. queries: pairs covered by the dashed hops (discussed in the text).
#  (labels=None: the greedy densest-subgraph cover is not deterministic enough
#   for verbatim comparison; rely on Layers 1–2.)
#  Validate:  pytest tests/paper_examples/test_runner.py -k twohop -v
#  If it fails with "transcription error", the error is in YOUR transcription
#  (graph or labels), not in the library — re-check the figure.
#  Portuguese guide: README_pt.md in this folder.
# =============================================================================
from _schema import PaperExample

EXAMPLE = PaperExample(
    method="twohop",
    source="Cohen, Halperin, Kaplan, Zwick, SICOMP 2003 — Reachability and Distance Queries via 2-Hop Labels",
    figure="Figure 1, p. 5",
    doi="10.1137/S0097539702403098",
    num_nodes=None,                       # <- STUDENT
    edges=[],                             # <- STUDENT (verbatim from the figure)
    queries=[],                           # <- STUDENT (pairs highlighted in the text)
    labels=None,
)
