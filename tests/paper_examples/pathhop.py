# =============================================================================
# COMO PREENCHER (aluno) — Path-Hop
# Artigo: docs/path-hop.pdf — abrir em: páginas 3–6, "Figures 1–4" (chain decomposition, RTC, hop cover, path-hop).
#  1. edges: transcreva o grafo base das Figures 1–2.
#  2. num_nodes: maior id + 1.
#  3. queries: pares que o texto resolve via árvore + hops.
#  (labels=None por ora.)
#  Valide:  pytest tests/paper_examples/test_runner.py -k pathhop -v
#  Se falhar com "transcription error", o erro está na SUA transcrição
#  (grafo ou rótulos), não na biblioteca — reconfira a figura.
# =============================================================================
from _schema import PaperExample

EXAMPLE = PaperExample(
    method="pathhop",
    source="Cai & Poon, CIKM 2010 — Path-Hop",
    figure="Figures 1–4, pp. 3–6",
    doi="10.1145/1871437.1871457",
    num_nodes=None,                       # <- ALUNO
    edges=[],                             # <- ALUNO (verbatim da figura)
    queries=[],                           # <- ALUNO (pares destacados no texto)
    labels=None,
)
