# =============================================================================
# HL (Hierarchical Labeling) — EXEMPLO DE REFERÊNCIA (preenchido)
# Artigo: docs/DL.pdf — página 5 (numerada 1982), "Figure 1".
#
# Transcrição: Claude (leitura da figura renderizada a 600 dpi, por quadrantes),
# 2026-07-10. O cross-check de transcrição valida a consistência entre o grafo
# (Figure 1a) e a tabela de rótulos (Figure 1d) em todos os pares dos vértices
# transcritos da tabela — os dois foram copiados de fontes independentes da
# mesma figura, então a concordância é uma evidência forte de leitura correta.
#
# ATENÇÃO (revisão humana bem-vinda):
#  - Arestas de leitura mais difícil na figura: 6->13 e 11->12 (na região
#    congestionada entre 6, 11 e 13). O cross-check não as discrimina porque
#    nenhum par transcrito da tabela passa exclusivamente por elas.
#  - A tabela da Figure 1d é PARCIAL (linha "..."), por isso labels.expected
#    tem só os vértices impressos e mode="invariant" (o FastCover do backbone
#    tem liberdade de desempate, então os rótulos construídos podem diferir
#    dos impressos e ainda estar corretos; o invariante exige que induzam a
#    MESMA alcançabilidade nos vértices transcritos).
# =============================================================================
from _schema import PaperExample, LabelCheck

EXAMPLE = PaperExample(
    method="hl",
    source="Jin & Wang, PVLDB 2013 — Simple, Fast, and Scalable Reachability Oracle",
    figure="Figure 1, p. 1982",
    doi="10.14778/2556549.2556578",
    num_nodes=41,
    edges=[
        (0, 2), (0, 3), (0, 6),
        (1, 3), (1, 4),
        (2, 5),
        (3, 7), (3, 9),
        (4, 9),
        (5, 6), (5, 10), (5, 11),
        (6, 7), (6, 13),          # 6->13: ver ATENÇÃO acima
        (7, 11), (7, 13), (7, 15),
        (8, 7), (8, 15),
        (9, 8), (9, 16),
        (10, 12),
        (11, 12),                 # 11->12: ver ATENÇÃO acima
        (12, 17), (12, 18),
        (13, 12), (13, 14), (13, 18),
        (14, 19),
        (15, 20),
        (16, 21),
        (17, 22),
        (18, 19), (18, 22), (18, 29),
        (19, 24),
        (20, 19), (20, 25),
        (21, 20), (21, 27),
        (22, 23),
        (23, 29),
        (24, 29),
        (25, 24), (25, 32), (25, 33), (25, 34),
        (26, 25), (26, 35),
        (27, 28),
        (28, 26),
        (29, 30), (29, 36),
        (30, 31),
        (31, 40),
        (32, 31),
        (33, 39),
        (34, 38),
        (35, 38),
        (36, 37),
        (38, 33),
        (39, 40),
        (40, 37),
    ],
    # Fatos deriváveis da tabela 1(d) (interseção Lout/Lin), conferidos à mão:
    queries=[
        (0, 8, True),    # Lout(0) contém 9, e 9 está em Lin(8): 0 -> 3 -> 9 -> 8
        (2, 6, True),    # Lout(2) contém 5, e 5 está em Lin(6): 2 -> 5 -> 6
        (2, 8, False),   # Lout(2) e Lin(8) não se intersectam
        (3, 6, False),   # Lout(3) e Lin(6) não se intersectam
        (6, 38, True),   # {7,25,35} em comum: 6 -> 7 -> 15 -> 20 -> 25 -> 34 -> 38
        (38, 0, False),  # Lout(38) = {33,38,39,40} não intersecta Lin(0)
    ],
    # Figure 1(d), "Hop Labeling for V0" — tabela parcial (linha "..."):
    labels=LabelCheck(
        kind="two_hop",
        mode="invariant",
        expected={
            0:  {"Lin": {0},               "Lout": {0, 2, 3, 5, 6, 7, 9, 17, 25, 27, 35, 40}},
            1:  {"Lin": {1},               "Lout": {1, 3, 4, 7, 9, 25, 27, 35, 40}},
            2:  {"Lin": {0, 2},            "Lout": {2, 5, 7, 17, 25, 35}},
            3:  {"Lin": {0, 1, 3},         "Lout": {3, 7, 9, 20, 25, 27, 35, 40}},
            4:  {"Lin": {1, 4},            "Lout": {4, 7, 9, 25, 27, 35, 40}},
            6:  {"Lin": {0, 5, 6},         "Lout": {6, 7, 14, 18, 25, 29, 35, 40}},
            8:  {"Lin": {8, 9},            "Lout": {7, 8, 15, 20, 25, 35, 40}},
            38: {"Lin": {7, 25, 34, 35, 38}, "Lout": {33, 38, 39, 40}},
        },
    ),
)
