"""Method catalog: a name -> ReachabilityIndex registry.

Methods register with the :func:`register` decorator and are discovered with
:func:`methods` / :func:`get`. This registry is what makes the library an
extensible catalog rather than a fixed set of methods.
"""
from .base import ReachabilityIndex

_REGISTRY: dict[str, type[ReachabilityIndex]] = {}


def register(cls: type[ReachabilityIndex]) -> type[ReachabilityIndex]:
    """Class decorator: register a ReachabilityIndex subclass by its `name`."""
    if not getattr(cls, "name", ""):
        raise ValueError(f"{cls.__name__} must define a non-empty `name`")
    _REGISTRY[cls.name] = cls
    return cls


def methods(kind: str = "all") -> list[str]:
    """Sorted list of registered method names.

    kind: "all" (default), "static", or "dynamic". A catalog that hid half its
    contents by default would be a worse lie than one that lists everything, so
    the default is "all" — callers that must not mix the two halves (benchmarks,
    whose build-once cost has no dynamic counterpart) ask for "static" explicitly.
    """
    # Imported here, not at module level, to keep this module importable from inside
    # `dynamic`. Today `dynamic.base` only reaches `..base`, which imports nothing of
    # ours, so a top-level import would in fact still work — but each method module
    # registers itself with `from .. import catalog` + `@catalog.register` (see
    # `static/other.py`), so once `dynamic/__init__` pulls in a method, a top-level
    # import here would close the cycle: catalog -> dynamic -> dynamic.feline_pk ->
    # catalog, while catalog is still half-initialised. Keeping it local costs a
    # cached sys.modules lookup and avoids the trap.
    from .dynamic.base import DynamicReachabilityIndex

    if kind == "all":
        return sorted(_REGISTRY)
    if kind == "dynamic":
        return sorted(n for n, c in _REGISTRY.items()
                      if issubclass(c, DynamicReachabilityIndex))
    if kind == "static":
        return sorted(n for n, c in _REGISTRY.items()
                      if not issubclass(c, DynamicReachabilityIndex))
    raise ValueError(f"kind must be 'all', 'static' or 'dynamic', not {kind!r}")


def get(name: str) -> type[ReachabilityIndex]:
    """Look up a registered method class by name (raises KeyError if unknown)."""
    return _REGISTRY[name]
