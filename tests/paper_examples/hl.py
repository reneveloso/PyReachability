# =============================================================================
# COMO PREENCHER (aluno) — HL (Hierarchical Labeling)
# Artigo: docs/DL.pdf — abrir em: página 5 (numerada 1982), "Figure 1".
#  1. edges: transcreva cada aresta u->v do grafo G0 (Figure 1a) como (u, v).
#     Confira duas vezes: uma aresta errada faz o cross-check reprovar.
#  2. num_nodes: maior id de vértice + 1.
#  3. queries: pares que o TEXTO destaca (Examples 4.2/4.3).
#  4. labels.expected: copie a tabela "Hop Labeling for V0" (Figure 1d):
#     para cada vértice v da tabela, {"Lin": {...}, "Lout": {...}}.
#     Se a tabela for parcial (linha "..."), use mode="invariant".
#  Valide:  pytest tests/paper_examples/test_runner.py -k hl -v
#  Se falhar com "transcription error", o erro está na SUA transcrição
#  (grafo ou rótulos), não na biblioteca — reconfira a figura.
# =============================================================================
from _schema import PaperExample, LabelCheck

EXAMPLE = PaperExample(
    method="hl",
    source="Jin & Wang, PVLDB 2013 — Simple, Fast, and Scalable Reachability Oracle",
    figure="Figure 1, p. 1982",
    doi="10.14778/2556549.2556578",
    num_nodes=None,                       # <- ALUNO
    edges=[],                             # <- ALUNO (verbatim da figura)
    queries=[],                           # <- ALUNO (pares destacados no texto)
    labels=LabelCheck(kind="two_hop", expected={}),
)
