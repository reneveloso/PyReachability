# =============================================================================
# COMO PREENCHER (aluno) — DL (Distribution Labeling)
# Artigo: docs/DL.pdf — abrir em: página 7, "Figure 2" (running example de Cov).
#  1. edges/num_nodes: o exemplo usa o MESMO G0 da Figure 1a (p. 5).
#  2. queries: os fatos do texto (Example 5.1: 7 -> 13; TC(13) ⊂ TC(7)).
#  (labels=None: a Figure 2 mostra conjuntos Cov, não a tabela Lin/Lout;
#   além disso DL==PLL no núcleo, com rótulos em espaço de ranks.)
#  Valide:  pytest tests/paper_examples/test_runner.py -k dl -v
#  Se falhar com "transcription error", o erro está na SUA transcrição
#  (grafo ou rótulos), não na biblioteca — reconfira a figura.
# =============================================================================
from _schema import PaperExample

EXAMPLE = PaperExample(
    method="dl",
    source="Jin & Wang, PVLDB 2013 — Simple, Fast, and Scalable Reachability Oracle",
    figure="Figure 2, p. 1984",
    doi="10.14778/2556549.2556578",
    num_nodes=None,                       # <- ALUNO
    edges=[],                             # <- ALUNO (verbatim da figura)
    queries=[],                           # <- ALUNO (pares destacados no texto)
    labels=None,
)
