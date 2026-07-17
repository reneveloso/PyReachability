"""PyReachability — fast graph reachability methods (C++17 core, Python API).

Build a :class:`Graph`, pick a method, call ``build`` then ``query``. Methods
share the :class:`ReachabilityIndex` interface and are discoverable through
:mod:`~pyreachability.catalog`.

Methods live in two subpackages, and the import says which half you are in:

>>> from pyreachability import Graph, catalog
>>> from pyreachability.static import GRAIL      # built once, then read-only
"""
from ._version import __version__
from ._core import Graph
from .base import ReachabilityIndex
from . import catalog
from . import static   # noqa: F401  — import side effect: @catalog.register
from . import dynamic  # noqa: F401  — import side effect: @catalog.register

__all__ = ["__version__", "Graph", "ReachabilityIndex", "catalog"]
