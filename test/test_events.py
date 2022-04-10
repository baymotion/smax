# test_events.py - See test_basic.py, except that
# the events are handled in the current
# state, instead of overall.

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
        self._c = False
    exit:
        # don't ever exit this thing;
        # the events exit the substates
        # but not this one.
        assert False
    ev_d -> s_d
    *state s_a:
        enter: self._a = True
        exit: self._a = False
        ev_b -> s_b
    state s_b:
        enter: self._b = True
        exit: self._b = False
        ev_a -> s_a
    # Nothing gets us here.
    state s_c:
        enter: self._c = True
        exit: self._c = False
    state s_d:
        ev_a -> s_a
        *state s_d_1:
            ev_x: log.debug("s_d_1: ev_x!")
        ---
        *state s_d_2:
            pass
        ---
        *state s_d_3:
            ev_x: log.debug("s_d_3: ev_x!")

%%
"""

def test_events():
    module = utils.compile_state_machine(__file__)
    class Test(utils.wrap(module.TestMachine)):
        def __init__(self, reactor):
            super(Test, self).__init__(reactor)
    reactor = smax.SelectReactor()
    test = Test(reactor)
    test._state_machine_debug_enable = True
    test.start()
    assert test._a == True
    assert test._b == False
    assert test._c == False
    # Now check for exactly the expected transitions.
    test.expected([
        (Test.ENTERED, "TestMachine"),
        (Test.ENTERED, "TestMachine.s_a"),
    ])

    test.ev_b()
    assert test._a == False
    assert test._b == True
    assert test._c == False
    test.expected([
        (Test.HANDLED, "TestMachine.s_a", "ev_b"),
        (Test.EXITED, "TestMachine.s_a"),
        (Test.ENTERED, "TestMachine.s_b"),
    ])

    test.ev_b()
    assert test._a == False
    assert test._b == True
    assert test._c == False
    test.expected([
        (Test.IGNORED, "ev_b"),
    ])

    test.ev_a()
    assert test._a == True
    assert test._b == False
    assert test._c == False
    test.expected([
        (Test.HANDLED, "TestMachine.s_b", "ev_a"),
        (Test.EXITED, "TestMachine.s_b"),
        (Test.ENTERED, "TestMachine.s_a"),
    ])

    test.ev_d()
    test.expected([
        (Test.HANDLED, "TestMachine", "ev_d"),
        (Test.EXITED, "TestMachine.s_a"),
        (Test.ENTERED, "TestMachine.s_d"),
        (Test.ENTERED, "TestMachine.s_d.s_d_1"),
        (Test.ENTERED, "TestMachine.s_d.s_d_2"),
        (Test.ENTERED, "TestMachine.s_d.s_d_3"),
    ])

    test.ev_x()
    test.expected([
        (Test.HANDLED, "TestMachine.s_d.s_d_1", "ev_x"),
        (Test.HANDLED, "TestMachine.s_d.s_d_3", "ev_x"),
    ])

    test.ev_a()
    test.expected([
        (Test.HANDLED, "TestMachine.s_d", "ev_a"),
        (Test.EXITED, "TestMachine.s_d.s_d_1"),
        (Test.EXITED, "TestMachine.s_d.s_d_2"),
        (Test.EXITED, "TestMachine.s_d.s_d_3"),
        (Test.EXITED, "TestMachine.s_d"),
        (Test.ENTERED, "TestMachine.s_a"),
    ])
