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


def methods() -> list[str]:
    """Sorted list of registered method names."""
    return sorted(_REGISTRY)


def get(name: str) -> type[ReachabilityIndex]:
    """Look up a registered method class by name (raises KeyError if unknown)."""
    return _REGISTRY[name]
