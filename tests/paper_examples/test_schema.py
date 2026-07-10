import pytest
from _schema import PaperExample, LabelCheck, derive_reach


def test_derive_reach_dag():
    # diamond: 0->1, 0->2, 1->3, 2->3
    reach = derive_reach(4, [(0, 1), (0, 2), (1, 3), (2, 3)])
    assert reach == {0: {1, 2, 3}, 1: {3}, 2: {3}, 3: set()}


def test_derive_reach_cycle_includes_self():
    # 0->1->0 is an SCC: each reaches the other AND itself via the cycle
    reach = derive_reach(3, [(0, 1), (1, 0), (1, 2)])
    assert reach[0] == {0, 1, 2}
    assert reach[1] == {0, 1, 2}
    assert reach[2] == set()


def test_is_filled():
    ex = PaperExample(method="x", source="s", figure="f", doi="d",
                      num_nodes=None, edges=[])
    assert not ex.is_filled
    ex2 = PaperExample(method="x", source="s", figure="f", doi="d",
                       num_nodes=2, edges=[(0, 1)])
    assert ex2.is_filled
