import pytest
from _schema import PaperExample
from test_runner import check_answers


def _diamond(method="bfsdfs", queries=()):
    return PaperExample(
        method=method, source="selftest", figure="-", doi="-",
        num_nodes=4, edges=[(0, 1), (0, 2), (1, 3), (2, 3)],
        queries=list(queries),
    )


def test_layer1_passes_on_correct_example():
    check_answers(_diamond())            # bfsdfs must reproduce the diamond


def test_layer2_checks_highlighted_queries():
    check_answers(_diamond(queries=[(0, 3, True), (3, 0, False)]))


def test_layer2_fails_on_wrong_expectation():
    with pytest.raises(AssertionError, match="query"):
        check_answers(_diamond(queries=[(3, 0, True)]))   # wrong on purpose


def test_unfilled_stub_skips():
    ex = PaperExample(method="bfsdfs", source="s", figure="f", doi="d",
                      num_nodes=None, edges=[])
    with pytest.raises(pytest.skip.Exception):
        check_answers(ex)
