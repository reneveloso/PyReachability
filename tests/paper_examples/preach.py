# =============================================================================
# COMO PREENCHER (aluno) — PReaCH
# Artigo: docs/preach.pdf — abrir em: página 6, "Figure 1" (example RCH) e página 7, "Figure 2" (níveis topológicos).
#  1. edges: transcreva o grafo de exemplo (Figure 1/2).
#  2. num_nodes: maior id + 1.
#  3. queries: pares que o texto decide por níveis/intervalos.
#  (labels=None por ora.)
#  Valide:  pytest tests/paper_examples/test_runner.py -k preach -v
#  Se falhar com "transcription error", o erro está na SUA transcrição
#  (grafo ou rótulos), não na biblioteca — reconfira a figura.
# =============================================================================
from _schema import PaperExample

EXAMPLE = PaperExample(
    method="preach",
    source="Merz & Sanders, ESA 2014 — PReaCH",
    figure="Figures 1–2, pp. 6–7",
    doi="10.1007/978-3-662-44777-2_58",
    num_nodes=None,                       # <- ALUNO
    edges=[],                             # <- ALUNO (verbatim da figura)
    queries=[],                           # <- ALUNO (pares destacados no texto)
    labels=None,
)
