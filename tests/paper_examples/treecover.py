# =============================================================================
# COMO PREENCHER (aluno) — Tree Cover (Agrawal)
# Artigo: docs/agrawal.pdf — abrir em: página 3, "Figure 3.3" (two different tree-covers for the same graph).
#  1. edges: transcreva o grafo da Figure 3.3.
#  2. num_nodes: maior id + 1 (mapeie letras -> inteiros se preciso; anote).
#  3. queries: pares que o texto usa ao explicar a compressão por intervalos.
#  (labels=None por ora: comparador "intervals" ainda não existe — ver README.)
#  Valide:  pytest tests/paper_examples/test_runner.py -k treecover -v
#  Se falhar com "transcription error", o erro está na SUA transcrição
#  (grafo ou rótulos), não na biblioteca — reconfira a figura.
# =============================================================================
from _schema import PaperExample

EXAMPLE = PaperExample(
    method="treecover",
    source="Agrawal, Borgida, Jagadish, SIGMOD 1989 — Efficient Management of Transitive Relationships",
    figure="Figure 3.3, p. 3",
    doi="10.1145/67544.66950",
    num_nodes=None,                       # <- ALUNO
    edges=[],                             # <- ALUNO (verbatim da figura)
    queries=[],                           # <- ALUNO (pares destacados no texto)
    labels=None,
)
