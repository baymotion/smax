# basic.py - Basic one-level state machine
# behavior:
#   ev_a goes to s_a,
#   ev_b goes to s_b.
# Proves that we go to the intended
# states and not the unintended ones.

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
    ev_a -> s_a
    ev_b -> s_b
    *state s_a:
        enter: self._a = True
        exit: self._a = False
    state s_b:
        enter: self._b = True
        exit: self._b = False
    # Nothing gets us here.
    state s_c:
        enter: self._c = True
        exit: self._c = False
%%
"""

import smax
from smax import log
import sys

def test_basic():
    module = utils.compile_state_machine(__file__)
    Test = utils.wrap(module.TestMachine)
    reactor = smax.SelectReactor()
    log.enable_trace = True
    test = Test(reactor)
    test._state_machine_debug_enable = True
    test.start()
    reactor.sync()
    assert test._a == True
    assert test._b == False
    assert test._c == False
    # Now check for exactly the expected transitions.
    test.expected([
        (Test.ENTERED, "TestMachine"),
        (Test.ENTERED, "TestMachine.s_a"),
    ])

    test.ev_b()
    reactor.sync()
    assert test._a == False
    assert test._b == True
    assert test._c == False
    test.expected([
        (Test.HANDLED, "TestMachine", "ev_b"),
        (Test.EXITED, "TestMachine.s_a"),
        (Test.ENTERED, "TestMachine.s_b"),
    ])

    test.ev_b()
    reactor.sync()
    assert test._a == False
    assert test._b == True
    assert test._c == False
    test.expected([
        (Test.HANDLED, "TestMachine", "ev_b"),
        (Test.EXITED, "TestMachine.s_b"),
        (Test.ENTERED, "TestMachine.s_b"),
    ])

    test.ev_a()
    reactor.sync()
    assert test._a == True
    assert test._b == False
    assert test._c == False
    test.expected([
        (Test.HANDLED, "TestMachine", "ev_a"),
        (Test.EXITED, "TestMachine.s_b"),
        (Test.ENTERED, "TestMachine.s_a"),
    ])