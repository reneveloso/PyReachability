# =============================================================================
# COMO PREENCHER (aluno) — 2-Hop (Cohen et al.)
# Artigo: docs/2-hop.pdf — abrir em: página 5, "Figure 1" (solid = arestas do grafo, dashed = hops).
#  1. edges: transcreva SÓ as arestas sólidas da Figure 1.
#  2. num_nodes: maior id + 1.
#  3. queries: pares cobertos pelos hops tracejados (o texto os discute).
#  (labels=None: a cobertura gulosa densest-subgraph não é determinística o
#   bastante para comparação verbatim; use as Camadas 1–2.)
#  Valide:  pytest tests/paper_examples/test_runner.py -k twohop -v
#  Se falhar com "transcription error", o erro está na SUA transcrição
#  (grafo ou rótulos), não na biblioteca — reconfira a figura.
# =============================================================================
from _schema import PaperExample

EXAMPLE = PaperExample(
    method="twohop",
    source="Cohen, Halperin, Kaplan, Zwick, SICOMP 2003 — Reachability and Distance Queries via 2-Hop Labels",
    figure="Figure 1, p. 5",
    doi="10.1137/S0097539702403098",
    num_nodes=None,                       # <- ALUNO
    edges=[],                             # <- ALUNO (verbatim da figura)
    queries=[],                           # <- ALUNO (pares destacados no texto)
    labels=None,
)
