"""Static reachability indexes — built once over an immutable graph.

Grouped by the index classes of the survey this catalog follows (Zhang,
Bonifati, Ozsu, ACM Computing Surveys 58(6), 2025, Table 1), so that this
package mirrors `docs/methods.md` section for section.
"""
from .baselines import BFSDFS, TC
from .tree_cover import (TreeCover, GRAIL, TreeSSPI, DualLabeling, GRIPP,
                         PathTree, Ferrari)
from .two_hop import PLL, TwoHop, ThreeHop, PathHop, TFLabel, DL, HL, TOL, OReach
from .approximate_tc import IP, BFL
from .chain_cover import ChainCover, OptimalChainCover
from .other import FELINE, PReaCH

__all__ = ["BFSDFS", "TC",
           "TreeCover", "GRAIL", "TreeSSPI", "DualLabeling", "GRIPP",
           "PathTree", "Ferrari",
           "PLL", "TwoHop", "ThreeHop", "PathHop", "TFLabel", "DL", "HL",
           "TOL", "OReach",
           "IP", "BFL",
           "ChainCover", "OptimalChainCover",
           "FELINE", "PReaCH"]
