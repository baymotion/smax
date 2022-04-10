# test_overflow.py - What happens if we have a perpetual loop?

import smax
import utils

r"""
%%

machine TestMachine:
    *state s_a:
        -> s_b
    state s_b:
        -> s_a
%%
"""

def test_basic():
    module = utils.compile_state_machine(__file__)
    Test = utils.wrap(module.TestMachine)
    reactor = smax.SelectReactor()
    test = Test(reactor)
    try:
        test.start()
    except RecursionError as e:
        print("Caught %s (%s), as expected" % (type(e).__name__, e))
        pass
    else:
        assert False
