"""PyReachability — fast graph reachability methods (C++17 core, Python API).

Build a :class:`Graph`, pick a method (e.g. :class:`BFSDFS`), call ``build`` then
``query``. Methods share the :class:`ReachabilityIndex` interface and are discoverable
through :mod:`~pyreachability.catalog`.
"""
from ._version import __version__
from ._core import (Graph, _BFSDFSCore, _GRAILCore, _FelineCore, _PLLCore,
                    _TCCore, _TreeCoverCore, _BFLCore, _ChainCoverCore, _PReaCHCore,
                    _TwoHopCore, _TFLabelCore, _TOLCore, _HLCore, _OReachCore,
                    _ThreeHopCore, _PathHopCore, _FerrariCore, _DualLabelingCore,
                    _TreeSSPICore, _GRIPPCore, _PathTreeCore, _IPCore,
                    _OptimalChainCoverCore)
from .base import ReachabilityIndex
from . import catalog
from .static import (BFSDFS, TC,
                     TreeCover, GRAIL, TreeSSPI, DualLabeling, GRIPP,
                     PathTree, Ferrari,
                     PLL, TwoHop, ThreeHop, PathHop, TFLabel, DL, HL, TOL, OReach,
                     IP, BFL, ChainCover, OptimalChainCover, FELINE, PReaCH)   # temporary: removed in Task 5
import numpy as np



__all__ = ["__version__", "Graph", "ReachabilityIndex", "catalog",
           "BFSDFS", "GRAIL", "FELINE", "PLL", "TC", "TreeCover", "BFL",
           "ChainCover", "PReaCH", "TwoHop", "TFLabel", "TOL", "HL", "OReach",
           "ThreeHop", "PathHop", "Ferrari", "DualLabeling", "TreeSSPI", "GRIPP",
           "PathTree", "IP", "OptimalChainCover", "DL"]
