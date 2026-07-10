# =============================================================================
# COMO PREENCHER (aluno) — 3-Hop
# Artigo: docs/3-hop.pdf — abrir em: página 4, "Figure 1" (a simple example for 3-hop and 2-hop).
#  1. edges: transcreva o grafo da Figure 1.
#  2. num_nodes: maior id + 1.
#  3. queries: pares resolvidos via cadeias-rodovia no texto.
#  (labels=None por ora.)
#  Valide:  pytest tests/paper_examples/test_runner.py -k threehop -v
#  Se falhar com "transcription error", o erro está na SUA transcrição
#  (grafo ou rótulos), não na biblioteca — reconfira a figura.
# =============================================================================
from _schema import PaperExample

EXAMPLE = PaperExample(
    method="threehop",
    source="Jin, Xiang, Ruan, Fuhry, SIGMOD 2009 — 3-HOP",
    figure="Figure 1, p. 4",
    doi="10.1145/1559845.1559930",
    num_nodes=None,                       # <- ALUNO
    edges=[],                             # <- ALUNO (verbatim da figura)
    queries=[],                           # <- ALUNO (pares destacados no texto)
    labels=None,
)
