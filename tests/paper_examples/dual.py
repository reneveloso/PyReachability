# =============================================================================
# COMO PREENCHER (aluno) — Dual Labeling
# Artigo: docs/Dual_Labeling_Answering_Graph_Reachability_Queries_in_Constant_Time.pdf — abrir em: página 4, "Figure 1" (input graph) e "Figure 2" (spanning tree com intervalos).
#  1. edges: transcreva o grafo da Figure 1.
#  2. num_nodes: maior id + 1.
#  3. queries: pares usados no texto ao explicar tree-labels vs non-tree links.
#  (labels=None por ora: o índice é intervalos + tabela de links transitivos —
#   comparador próprio no futuro.)
#  Valide:  pytest tests/paper_examples/test_runner.py -k dual -v
#  Se falhar com "transcription error", o erro está na SUA transcrição
#  (grafo ou rótulos), não na biblioteca — reconfira a figura.
# =============================================================================
from _schema import PaperExample

EXAMPLE = PaperExample(
    method="dual",
    source="Wang, He, Yang, Yu, Yu, ICDE 2006 — Dual Labeling",
    figure="Figures 1–2, p. 4",
    doi="10.1109/ICDE.2006.53",
    num_nodes=None,                       # <- ALUNO
    edges=[],                             # <- ALUNO (verbatim da figura)
    queries=[],                           # <- ALUNO (pares destacados no texto)
    labels=None,
)
