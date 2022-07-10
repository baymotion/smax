# test_overflow.py - What happens if we have a perpetual loop?

import smax
import utils

smax.log.enable_debug = False

r"""
%%

machine TestMachine:
    enter: self._count = 0
    *state s_a:
        enter: self._count += 1
        -> s_b
    state s_b:
        enter: self._count += 1
        -> s_a


machine OkMachine:
    enter: self._count = 0
    *state s_a:
        enter: self._count += 1
        s(0) -> s_b
    state s_b:
        enter: self._count += 1
        s(0) -> s_a

%%
"""


def test_overflow():
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
    print("test._count=%s" % (test._count,))

    Ok = utils.wrap(module.OkMachine)
    ok = Ok(reactor)
    ok.start()

    def check():
        print("ok._count=%s" % (ok._count,))
        if ok._count < (10 * test._count):
            reactor.after_s(1, check)
            return
        reactor.stop()

    reactor.after_s(1, check)
    reactor.run()
