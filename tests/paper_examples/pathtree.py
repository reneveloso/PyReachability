# =============================================================================
# COMO PREENCHER (aluno) — Path-Tree
# Artigo: docs/path-tree.pdf — abrir em: páginas 13–15, "Fig. 5" e "Fig. 6" (complete labeling for the path-tree).
#  1. edges: transcreva o grafo dos exemplos (Fig. 4a/5).
#  2. num_nodes: maior id + 1.
#  3. queries: pares que o texto resolve com os rótulos 3-tupla.
#  (labels=None por ora: rótulos 3-tupla teriam comparador próprio no futuro.)
#  Valide:  pytest tests/paper_examples/test_runner.py -k pathtree -v
#  Se falhar com "transcription error", o erro está na SUA transcrição
#  (grafo ou rótulos), não na biblioteca — reconfira a figura.
# =============================================================================
from _schema import PaperExample

EXAMPLE = PaperExample(
    method="pathtree",
    source="Jin, Ruan, Xiang, Wang, ACM TODS 2011 — Path-Tree",
    figure="Figs. 5–6, pp. 13–15",
    doi="10.1145/1929934.1929941",
    num_nodes=None,                       # <- ALUNO
    edges=[],                             # <- ALUNO (verbatim da figura)
    queries=[],                           # <- ALUNO (pares destacados no texto)
    labels=None,
)
