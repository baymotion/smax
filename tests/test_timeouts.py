# timeouts.py

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
        self._c_100 = False
        self._c_200 = False
    exit:
        # don't ever exit this thing;
        # the events exit the substates
        # but not this one.
        assert False
    ev_c -> s_c
    *state s_a:
        enter: self._a = True
        exit: self._a = False
        ms(10) -> s_b
    state s_b:
        enter: self._b = True
        exit: self._b = False
    state s_c:
        ms(100): self._c_100 = True
        ms(150) [False]: assert False
        ms(200): self._c_200 = True
        ms(300) -> s_d
    state s_d:
        pass
%%
"""


def test_timeouts():
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
    reactor.sync()
    assert test._a
    assert not test._b

    def check(test=test):
        assert not test._a
        assert test._b
        assert not test._c_100
        assert not test._c_200
        test.expected(
            [
                (Test.ENTERED, "TestMachine"),
                (Test.ENTERED, "TestMachine.s_a"),
                (Test.TIMED_OUT, "TestMachine.s_a", "10ms"),
                (Test.EXITED, "TestMachine.s_a"),
                (Test.ENTERED, "TestMachine.s_b"),
            ]
        )
        test.ev_c()
        reactor.after_s(0.5, check_c)

    def check_c(test=test):
        assert not test._a
        assert not test._b
        assert test._c_100
        assert test._c_200
        test.expected(
            [
                (Test.HANDLED, "TestMachine", "ev_c"),
                (Test.EXITED, "TestMachine.s_b"),
                (Test.ENTERED, "TestMachine.s_c"),
                (Test.TIMED_OUT, "TestMachine.s_c", "100ms"),
                (Test.TIMED_OUT, "TestMachine.s_c", "200ms"),
                (Test.TIMED_OUT, "TestMachine.s_c", "300ms"),
                (Test.EXITED, "TestMachine.s_c"),
                (Test.ENTERED, "TestMachine.s_d"),
            ]
        )
        reactor.stop()

    reactor.after_s(0.5, check)
    reactor.run()
