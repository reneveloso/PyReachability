# =============================================================================
# HL (Hierarchical Labeling) — REFERENCE EXAMPLE (filled)
# Paper: docs/DL.pdf — page 5 (numbered 1982), "Figure 1".
#
# Transcription: Claude (reading the figure rendered at 600 dpi, quadrant by
# quadrant), 2026-07-10. The transcription cross-check validates consistency
# between the graph (Figure 1a) and the label table (Figure 1d) on every pair
# of the table's transcribed vertices — the two were copied independently from
# the same figure, so their agreement is strong evidence of a correct reading.
#
# CAUTION (human review welcome):
#  - Hardest-to-read edges in the figure: 6->13 and 11->12 (in the congested
#    region between 6, 11 and 13). The cross-check cannot discriminate them
#    because no transcribed table pair passes exclusively through them.
#  - The Figure 1d table is PARTIAL ("..." row), hence labels.expected holds
#    only the printed vertices and mode="invariant" (the backbone's FastCover
#    has tie-breaking freedom, so the built labels may differ from the printed
#    ones while still being correct; the invariant requires them to induce the
#    SAME reachability over the transcribed vertices).
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
        (6, 7), (6, 13),          # 6->13: see CAUTION above
        (7, 11), (7, 13), (7, 15),
        (8, 7), (8, 15),
        (9, 8), (9, 16),
        (10, 12),
        (11, 12),                 # 11->12: see CAUTION above
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
    # Facts derivable from table 1(d) (Lout/Lin intersection), checked by hand:
    queries=[
        (0, 8, True),    # Lout(0) contains 9, and 9 is in Lin(8): 0 -> 3 -> 9 -> 8
        (2, 6, True),    # Lout(2) contains 5, and 5 is in Lin(6): 2 -> 5 -> 6
        (2, 8, False),   # Lout(2) and Lin(8) do not intersect
        (3, 6, False),   # Lout(3) and Lin(6) do not intersect
        (6, 38, True),   # {7,25,35} in common: 6 -> 7 -> 15 -> 20 -> 25 -> 34 -> 38
        (38, 0, False),  # Lout(38) = {33,38,39,40} does not intersect Lin(0)
    ],
    # Figure 1(d), "Hop Labeling for V0" — partial table ("..." row):
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
