# test_substates.py - testing for substates.

import smax
import utils

r"""
%%

import smax.log as log

machine TestMachine:
    enter:
        log.debug("entering.")
        self._a = False
        self._a_1 = False
        self._a_2 = False
        self._b = False
        self._c = False
    exit:
        # don't ever exit this thing;
        # the events exit the substates
        # but not this one.
        assert False
    *state s_a:
        enter: self._a = True
        exit: self._a = False
        ev_b -> s_b
        *state s_a_1:
            enter: self._a_1 = True
            exit: self._a_1 = False
            ev_a_2 -> s_a_2
        state s_a_2:
            enter: self._a_2 = True
            exit: self._a_2 = False
            ev_a_1 -> s_a_1
    state s_b:
        enter: self._b = True
        exit: self._b = False
        ev_a -> s_a
    # Nothing gets us here.
    state s_c:
        enter: self._c = True
        exit: self._c = False
%%
"""

def test_substates():
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
    assert test._a == True
    assert test._a_1 == True
    assert test._a_2 == False
    assert test._b == False
    assert test._c == False
    # Now check for exactly the expected transitions.
    test.expected([
        (Test.ENTERED, "TestMachine"),
        (Test.ENTERED, "TestMachine.s_a"),
        (Test.ENTERED, "TestMachine.s_a.s_a_1"),
    ])

    test.ev_b()
    assert test._a == False
    assert test._a_1 == False
    assert test._a_2 == False
    assert test._b == True
    assert test._c == False
    test.expected([
        (Test.HANDLED, "TestMachine.s_a", "ev_b"),
        (Test.EXITED, "TestMachine.s_a.s_a_1"),
        (Test.EXITED, "TestMachine.s_a"),
        (Test.ENTERED, "TestMachine.s_b"),
    ])

    test.ev_b()
    assert test._a == False
    assert test._a_1 == False
    assert test._a_2 == False
    assert test._b == True
    assert test._c == False
    test.expected([
        (Test.IGNORED, "ev_b"),
    ])

    test.ev_a()
    assert test._a == True
    assert test._a_1 == True
    assert test._a_2 == False
    assert test._b == False
    assert test._c == False
    test.expected([
        (Test.HANDLED, "TestMachine.s_b", "ev_a"),
        (Test.EXITED, "TestMachine.s_b"),
        (Test.ENTERED, "TestMachine.s_a"),
        (Test.ENTERED, "TestMachine.s_a.s_a_1"),
    ])

    test.ev_a_1()
    assert test._a == True
    assert test._a_1 == True
    assert test._a_2 == False
    assert test._b == False
    assert test._c == False
    test.expected([
        (Test.IGNORED, "ev_a_1"),
    ])

    test.ev_a_2()
    assert test._a == True
    assert test._a_1 == False
    assert test._a_2 == True
    assert test._b == False
    assert test._c == False
    test.expected([
        (Test.HANDLED, "TestMachine.s_a.s_a_1", "ev_a_2"),
        (Test.EXITED, "TestMachine.s_a.s_a_1"),
        (Test.ENTERED, "TestMachine.s_a.s_a_2"),
    ])

    test.ev_b()
    assert test._a == False
    assert test._a_1 == False
    assert test._a_2 == False
    assert test._b == True
    assert test._c == False
    test.expected([
        (Test.HANDLED, "TestMachine.s_a", "ev_b"),
        (Test.EXITED, "TestMachine.s_a.s_a_2"),
        (Test.EXITED, "TestMachine.s_a"),
        (Test.ENTERED, "TestMachine.s_b"),
    ])
