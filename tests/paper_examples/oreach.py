# =============================================================================
# COMO PREENCHER (aluno) — O'Reach
# Artigo: docs/oreach.pdf — abrir em: página 7, "Figure 1" (extended topological sorting example).
#  1. edges: transcreva o grafo da Figure 1.
#  2. num_nodes: maior id + 1.
#  3. queries: pares que as observações O(1) do texto decidem.
#  (labels=None: as observações usam vértices de suporte escolhidos
#   heuristicamente — não reproduzíveis verbatim.)
#  Valide:  pytest tests/paper_examples/test_runner.py -k oreach -v
#  Se falhar com "transcription error", o erro está na SUA transcrição
#  (grafo ou rótulos), não na biblioteca — reconfira a figura.
# =============================================================================
from _schema import PaperExample

EXAMPLE = PaperExample(
    method="oreach",
    source="Hanauer, Schulz, Trummer, ACM JEA 2022 — O'Reach",
    figure="Figure 1, p. 7",
    doi="10.1145/3556540",
    num_nodes=None,                       # <- ALUNO
    edges=[],                             # <- ALUNO (verbatim da figura)
    queries=[],                           # <- ALUNO (pares destacados no texto)
    labels=None,
)
