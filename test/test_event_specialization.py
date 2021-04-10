# test_event_specialization.py

import smax
import smax.log as log
import utils

# Sending ev_general always goes to s_general;
# Sending ev_specific in any state except s_b
#   goes to s_general with parameter==0,
# sending ev_specific in s_b goes to s_specific
#   with parameter==0.

r"""
%%

import smax.log as log

machine TestMachine:
    enter:
        log.debug("entering.")
        self._a = False
        self._general_parameter = None
        self._general = False
        self._b = False
        self._specific = False
    exit:
        # don't ever exit this thing;
        # the events exit the substates
        # but not this one.
        assert False
    ev_general(parameter) -> s_general:
        self._general_parameter = parameter
    ev_reset -> s_a
    ev_b -> s_b
    *state s_a:
        enter: self._a = True
        exit: self._a = False
    state s_general:
        enter: self._general = True
        exit: self._general = False
    state s_b:
        enter: self._b = True
        exit: self._b = False
        ev_specific is ev_general(0) -> s_specific
    state s_specific:
        enter: self._specific = True
        exit: self._specific = False
%%
"""

def test_event_specialization():
    module = utils.compile_state_machine(__file__)
    class Test(utils.wrap(module.TestMachine)):
        def __init__(self, reactor):
            super(Test, self).__init__(reactor)
            self._started = False
            self._done = False
    reactor = smax.SelectReactor()
    test = Test(reactor)
    test.start()
    assert test._a == True
    assert test._general == False
    assert test._general_parameter == None
    assert test._b == False
    assert test._specific == False

    test.expected([
        (Test.ENTERED, "TestMachine"),
        (Test.ENTERED, "TestMachine.s_a")
    ])

    test.ev_general(1)
    assert test._a == False
    assert test._general == True
    assert test._general_parameter == 1
    assert test._b == False
    assert test._specific == False
    test.expected([
        (Test.HANDLED, "TestMachine", "ev_general"),
        (Test.EXITED, "TestMachine.s_a"),
        (Test.ENTERED, "TestMachine.s_general"),
    ])

    test.ev_reset()
    assert test._a == True
    assert test._general == False
    assert test._general_parameter == 1
    assert test._b == False
    assert test._specific == False
    test.expected([
        (Test.HANDLED, "TestMachine", "ev_reset"),
        (Test.EXITED, "TestMachine.s_general"),
        (Test.ENTERED, "TestMachine.s_a"),
    ])

    # in this case, ev_specific is handled as ev_general(0)
    test.ev_specific()
    assert test._a == False
    assert test._general == True
    assert test._general_parameter == 0
    assert test._b == False
    assert test._specific == False
    test.expected([
        (Test.HANDLED, "TestMachine", "ev_general"), # because ev_specific wasn't handled
        (Test.EXITED, "TestMachine.s_a"),
        (Test.ENTERED, "TestMachine.s_general"),
    ])

    test.ev_b()
    assert test._a == False
    assert test._general == False
    assert test._general_parameter == 0
    assert test._b == True
    assert test._specific == False
    test.expected([
        (Test.HANDLED, "TestMachine", "ev_b"),
        (Test.EXITED, "TestMachine.s_general"),
        (Test.ENTERED, "TestMachine.s_b"),
    ])

    test.ev_specific()
    assert test._a == False
    assert test._general == False
    assert test._general_parameter == 0
    assert test._b == False
    assert test._specific == True
    test.expected([
        (Test.HANDLED, "TestMachine.s_b", "ev_specific"),
        (Test.EXITED, "TestMachine.s_b"),
        (Test.ENTERED, "TestMachine.s_specific"),
    ])

    test.ev_b()
    assert test._a == False
    assert test._general == False
    assert test._general_parameter == 0
    assert test._b == True
    assert test._specific == False
    test.expected([
        (Test.HANDLED, "TestMachine", "ev_b"),
        (Test.EXITED, "TestMachine.s_specific"),
        (Test.ENTERED, "TestMachine.s_b"),
    ])

    test.ev_general(2)
    assert test._a == False
    assert test._general == True
    assert test._general_parameter == 2
    assert test._b == False
    assert test._specific == False
    test.expected([
        (Test.HANDLED, "TestMachine", "ev_general"),
        (Test.EXITED, "TestMachine.s_b"),
        (Test.ENTERED, "TestMachine.s_general"),
    ])
