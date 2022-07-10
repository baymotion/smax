# test_constant - Verify that constant declarations
# work as expected and the topmost
# state machine enter code runs.

import smax
import utils

r"""
%%

CONSTANT_1 = 1

# This is a comment.
machine TestMachine:
    enter:
        assert CONSTANT_1 == 1
        self._started = True
%%
"""


def test_constant():
    module = utils.compile_state_machine(__file__)

    class Test(utils.wrap(module.TestMachine)):
        def __init__(self, reactor):
            super(Test, self).__init__(reactor)

    reactor = smax.SelectReactor()
    test = Test(reactor)
    test._state_machine_debug_enable = True
    test.start()
    assert test._started
    # Check for exactly the expected transitions.
    test.expected([(Test.ENTERED, Test.TestMachine)])
    test.end()
    test.expected([(Test.EXITED, Test.TestMachine)])
