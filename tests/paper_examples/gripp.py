# =============================================================================
# COMO PREENCHER (aluno) — GRIPP
# Artigo: docs/gripp.pdf — abrir em: página 4, "Figure 1" (Graph G and its GRIPP index table).
#  1. edges: transcreva o grafo G da Figure 1 (esquerda).
#  2. num_nodes: maior id + 1 (vértices por letra -> inteiros; anote o mapeamento).
#  3. queries: o texto avalia reach(D, r) na Figure 3 — inclua esses pares.
#  (labels=None por ora: o índice é a tabela de instâncias pré/pós-ordem.)
#  Valide:  pytest tests/paper_examples/test_runner.py -k gripp -v
#  Se falhar com "transcription error", o erro está na SUA transcrição
#  (grafo ou rótulos), não na biblioteca — reconfira a figura.
# =============================================================================
from _schema import PaperExample

EXAMPLE = PaperExample(
    method="gripp",
    source="Trißl & Leser, SIGMOD 2007 — Fast and Practical Indexing and Querying of Very Large Graphs",
    figure="Figure 1, p. 4",
    doi="10.1145/1247480.1247573",
    num_nodes=None,                       # <- ALUNO
    edges=[],                             # <- ALUNO (verbatim da figura)
    queries=[],                           # <- ALUNO (pares destacados no texto)
    labels=None,
)
