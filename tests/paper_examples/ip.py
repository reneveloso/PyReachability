# =============================================================================
# COMO PREENCHER (aluno) — IP (Independent Permutation)
# Artigo: docs/ip.pdf — abrir em: "Figure 1(a)" (grafo G) e página 7, "Figure 2" (Level Labels for G).
#  1. edges: transcreva o grafo G da Figure 1(a).
#  2. num_nodes: maior id + 1.
#  3. queries: pares discutidos no texto.
#  (labels=None: os rótulos k-min-wise são de permutação ALEATÓRIA — não são
#   reproduzíveis verbatim; os Level Labels da Figure 2 poderiam virar um
#   comparador próprio no futuro.)
#  Valide:  pytest tests/paper_examples/test_runner.py -k ip -v
#  Se falhar com "transcription error", o erro está na SUA transcrição
#  (grafo ou rótulos), não na biblioteca — reconfira a figura.
# =============================================================================
from _schema import PaperExample

EXAMPLE = PaperExample(
    method="ip",
    source="Wei, Yu, Lu, Jin, PVLDB 2014 — Reachability Querying: An Independent Permutation Labeling Approach",
    figure="Figure 1(a) + Figure 2, p. 7",
    doi="10.14778/2732977.2732992",
    num_nodes=None,                       # <- ALUNO
    edges=[],                             # <- ALUNO (verbatim da figura)
    queries=[],                           # <- ALUNO (pares destacados no texto)
    labels=None,
)
