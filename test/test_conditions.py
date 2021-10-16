# test_conditions.py - Ensure that conditions
# around transitions are handled per specification.

import smax
import utils

r"""
%%
import smax.log as log

# conditions are evaluated in the order given; the first one
# returning True is followed and circumvents testing of any
# of the rest
machine TestMachine:
    enter:
        log.debug("entering.")
    exit:
        assert False
    *state s_start:
        [ self.check_bad() ] -> s_bad
        [ self.check_more() ] -> s_bad
        -> s_check
        ms(1) -> s_bad
    state s_check:
        [ self.check_good() ] -> s_good
        -> s_bad
    state s_good:
        pass
    state s_bad:
        enter: assert False
%%
"""

def test_events():
    module = utils.compile_state_machine(__file__)
    class Test(utils.wrap(module.TestMachine)):
        def __init__(self, reactor):
            super(Test, self).__init__(reactor)
            self._checked_more = False
            self._checked_bad = False
        # this always happens first
        def check_bad(self):
            assert self._checked_bad==False
            assert self._checked_more==False
            self._checked_bad = True
            return False
        def check_more(self):
            assert self._checked_more==False
            assert self._checked_bad==True
            self._checked_more = True
            return False
        def check_good(self):
            return True
    reactor = smax.SelectReactor()
    test = Test(reactor)
    test._state_machine_debug_enable = True
    test.start()
    # Now check for exactly the expected transitions.
    test.expected([
        (Test.ENTERED, "TestMachine"),
        (Test.ENTERED, "TestMachine.s_start"),
        (Test.HANDLED, "TestMachine.s_start", None),
        (Test.EXITED, "TestMachine.s_start"),
        (Test.ENTERED, "TestMachine.s_check"),
        (Test.HANDLED, "TestMachine.s_check", None),
        (Test.EXITED, "TestMachine.s_check"),
        (Test.ENTERED, "TestMachine.s_good"),
    ])
