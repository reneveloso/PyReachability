"""Static reachability indexes — built once over an immutable graph.

Grouped by the index classes of the survey this catalog follows (Zhang,
Bonifati, Ozsu, ACM Computing Surveys 58(6), 2025, Table 1), so that this
package mirrors `docs/methods.md` section for section.
"""
from .baselines import BFSDFS, TC

__all__ = ["BFSDFS", "TC"]
