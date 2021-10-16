#
# test_debounce.py - Instantiate several switch debouncing
#   machines.
#

import smax
from smax import log
import utils

r"""
%%

import smax.log as log

macro DebouncedSwitch:
    enter:
        log.trace("DebouncedSwitch: enter")
    exit:
        log.trace("DebouncedSwitch: exit")
    [is_down()] -> s_down
    *state s_up:
        enter:
            self.ignore()
            self.up()
        ev_up: pass
        ev_down: pass
        ms(2) -> s_up_ready
    state s_up_ready:
        enter:
            self.listen()
        [is_down()] -> s_down
        ev_up: pass
        ev_down: s_down
    state s_down:
        enter: self.down()
        ev_up: pass
        ev_down: pass
    state s_down_ready:
        [not is_down()] -> s_up
        ev_up: s_up
        ev_down: pass

machine TestMachine:
    enter:
        log.trace("entering.")
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

def test_debounce():
    module = utils.compile_state_machine(__file__)
    Test = utils.wrap(module.TestMachine)
    reactor = smax.SelectReactor()
    test = Test(reactor)
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
        (Test.HANDLED, "TestMachine", "ev_b"),
        (Test.EXITED, "TestMachine.s_a"),
        (Test.ENTERED, "TestMachine.s_b"),
    ])

    test.ev_b()
    assert test._a == False
    assert test._b == True
    assert test._c == False
    test.expected([
        (Test.HANDLED, "TestMachine", "ev_b"),
        (Test.EXITED, "TestMachine.s_b"),
        (Test.ENTERED, "TestMachine.s_b"),
    ])

    test.ev_a()
    assert test._a == True
    assert test._b == False
    assert test._c == False
    test.expected([
        (Test.HANDLED, "TestMachine", "ev_a"),
        (Test.EXITED, "TestMachine.s_b"),
        (Test.ENTERED, "TestMachine.s_a"),
    ])
