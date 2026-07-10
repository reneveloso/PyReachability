# =============================================================================
# COMO PREENCHER (aluno) — FELINE
# Artigo: docs/paper_166.pdf — abrir em: página 4, "Figure 2" (DAG pequeno com coordenadas) e "Figure 3".
#  1. edges: transcreva o DAG da Figure 2(A).
#  2. num_nodes: maior id + 1 (atenção: a figura rotula vértices por letra?
#     mapeie letras -> inteiros em ordem alfabética e anote o mapeamento aqui).
#  3. queries: pares discutidos no texto (regiões de dominância, exceções da Fig. 4).
#  (labels=None por ora: comparador "coords_2d" ainda não existe — ver README.)
#  Valide:  pytest tests/paper_examples/test_runner.py -k feline -v
#  Se falhar com "transcription error", o erro está na SUA transcrição
#  (grafo ou rótulos), não na biblioteca — reconfira a figura.
# =============================================================================
from _schema import PaperExample

EXAMPLE = PaperExample(
    method="feline",
    source="Veloso, Cerf, Meira Jr., Zaki, EDBT 2014 — Reachability Queries in Very Large Graphs",
    figure="Figures 2–3, p. 4",
    doi="10.5441/002/edbt.2014.46",
    num_nodes=None,                       # <- ALUNO
    edges=[],                             # <- ALUNO (verbatim da figura)
    queries=[],                           # <- ALUNO (pares destacados no texto)
    labels=None,
)
