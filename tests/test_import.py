import pytest


def test_import_and_version():
    import pyreachability
    assert isinstance(pyreachability.__version__, str)
    assert pyreachability.__version__


def test_core_extension_loads():
    from pyreachability import _core
    assert _core.ping() == "pong"


def test_root_all_is_exactly_the_facade():
    import pyreachability
    assert pyreachability.__all__ == ["__version__", "Graph", "ReachabilityIndex", "catalog"]


def test_root_no_longer_exports_methods():
    with pytest.raises(ImportError):
        from pyreachability import GRAIL  # noqa: F401
