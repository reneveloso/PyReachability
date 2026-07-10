# =============================================================================
# HOW TO FILL IN (student) — Optimal Chain Cover (Chen & Chen)
# Paper: docs/An_Efficient_Algorithm_for_Answering_Graph_Reachability_Queries.pdf — open at: page 3, "Fig. 1" (DAG, transitive closure and graph encoding).
#  1. edges: transcribe the DAG of Fig. 1.
#  2. num_nodes: highest id + 1.
#  3. queries: pairs from the example.
#  4. BONUS: the method exposes num_chains(); the structural suite already
#     checks Dilworth's theorem.
#  (labels=None for now: "chains" comparator in the future.)
#  Validate:  pytest tests/paper_examples/test_runner.py -k optchain -v
#  If it fails with "transcription error", the error is in YOUR transcription
#  (graph or labels), not in the library — re-check the figure.
#  Portuguese guide: README_pt.md in this folder.
# =============================================================================
from _schema import PaperExample

EXAMPLE = PaperExample(
    method="optchain",
    source="Chen & Chen, ICDE 2008 — An Efficient Algorithm for Answering Graph Reachability Queries",
    figure="Fig. 1, p. 3",
    doi="10.1109/ICDE.2008.4497498",
    num_nodes=None,                       # <- STUDENT
    edges=[],                             # <- STUDENT (verbatim from the figure)
    queries=[],                           # <- STUDENT (pairs highlighted in the text)
    labels=None,
)
