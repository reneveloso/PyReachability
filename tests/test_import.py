def test_import_and_version():
    import pyreachability
    assert isinstance(pyreachability.__version__, str)
    assert pyreachability.__version__


def test_core_extension_loads():
    from pyreachability import _core
    assert _core.ping() == "pong"
