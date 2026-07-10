# =============================================================================
# COMO PREENCHER (aluno) — Ferrari
# Artigo: docs/ferrari.pdf — abrir em: "Fig. 1"–"Fig. 2" (grafo de exemplo com intervalos exatos/aproximados; nesta versão as legendas aparecem na p. 10).
#  1. edges: transcreva o grafo da Fig. 1.
#  2. num_nodes: maior id + 1.
#  3. queries: pares que o texto decide por intervalos exatos vs aproximados.
#  (labels=None por ora: comparador "intervals" futuro.)
#  Valide:  pytest tests/paper_examples/test_runner.py -k ferrari -v
#  Se falhar com "transcription error", o erro está na SUA transcrição
#  (grafo ou rótulos), não na biblioteca — reconfira a figura.
# =============================================================================
from _schema import PaperExample

EXAMPLE = PaperExample(
    method="ferrari",
    source="Seufert, Anand, Bedathur, Weikum, ICDE 2013 — FERRARI",
    figure="Figs. 1–2 (ver p. 10 desta versão)",
    doi="10.1109/ICDE.2013.6544893",
    num_nodes=None,                       # <- ALUNO
    edges=[],                             # <- ALUNO (verbatim da figura)
    queries=[],                           # <- ALUNO (pares destacados no texto)
    labels=None,
)
