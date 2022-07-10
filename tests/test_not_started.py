# test_not_started.py - Machines raise an exception if an
# event is called without being started.

import smax
import utils

r"""
%%
machine TestMachine:
    *state s_start:
        pass
    ev_a: assert False
%%
"""


def test_not_started():
    module = utils.compile_state_machine(__file__)
    Test = utils.wrap(module.TestMachine)
    reactor = smax.SelectReactor()
    test = Test(reactor)
    try:
        test.ev_a()
    except RuntimeError:
        return
    assert False and "Didn't trigger a runtime error."
