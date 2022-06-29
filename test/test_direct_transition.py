# test_direct_transition.py - queue up direct transitions

import smax
import utils

r"""
%%

import smax.log as log

machine TestMachine:
    enter:
        log.debug("entering.")
        self._a = False
        self._b = False
    exit:
        # don't ever exit this thing;
        # the events exit the substates
        # but not this one.
        assert False
    *state s_a:
        enter: self._a = True
        exit: self._a = False
        -> s_b
    state s_b:
        enter: self._b = True
        exit: self._b = False
%%
"""


def test_direct_transition():
    module = utils.compile_state_machine(__file__)

    class Test(utils.wrap(module.TestMachine)):
        def __init__(self, reactor):
            super(Test, self).__init__(reactor)
            self._started = False
            self._done = False

    reactor = smax.SelectReactor()
    test = Test(reactor)
    test._state_machine_debug_enable = True
    test.start()
    assert not test._a
    assert test._b

    # Now check for exactly the expected transitions.
    test.expected(
        [
            (Test.ENTERED, "TestMachine"),
            (Test.ENTERED, "TestMachine.s_a"),
            (Test.HANDLED, "TestMachine.s_a", None),
            (Test.EXITED, "TestMachine.s_a"),
            (Test.ENTERED, "TestMachine.s_b"),
        ]
    )
