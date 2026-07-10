# =============================================================================
# COMO PREENCHER (aluno) — Optimal Chain Cover (Chen & Chen)
# Artigo: docs/An_Efficient_Algorithm_for_Answering_Graph_Reachability_Queries.pdf — abrir em: página 3, "Fig. 1" (DAG, transitive closure and graph encoding).
#  1. edges: transcreva o DAG da Fig. 1.
#  2. num_nodes: maior id + 1.
#  3. queries: pares do exemplo.
#  4. BÔNUS: o método expõe num_chains(); a suíte estrutural já checa Dilworth.
#  (labels=None por ora: comparador "chains" futuro.)
#  Valide:  pytest tests/paper_examples/test_runner.py -k optchain -v
#  Se falhar com "transcription error", o erro está na SUA transcrição
#  (grafo ou rótulos), não na biblioteca — reconfira a figura.
# =============================================================================
from _schema import PaperExample

EXAMPLE = PaperExample(
    method="optchain",
    source="Chen & Chen, ICDE 2008 — An Efficient Algorithm for Answering Graph Reachability Queries",
    figure="Fig. 1, p. 3",
    doi="10.1109/ICDE.2008.4497498",
    num_nodes=None,                       # <- ALUNO
    edges=[],                             # <- ALUNO (verbatim da figura)
    queries=[],                           # <- ALUNO (pares destacados no texto)
    labels=None,
)
