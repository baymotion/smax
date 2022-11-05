# test_syntax.py - Try some tricky syntax things.

import smax
import utils

r"""
%%

import smax.log as log

machine A:
    enter: log.trace("enter A") ; self._x = True

machine B:
    enter:
        log.trace("enter B")
        if True:
            self._x = True
    ev_go: self.go()

machine C:
    ev_one:
        if True:
            self._x = True
    enter:
        pass
    *state s_one:
        -> s_two
    state s_two:
        enter: self.ev_one()

machine D:
    state s_later:
        enter: self._x = True
    ev_ignore:
        assert False and "Can't get here."
    *state s_earlier:
        -> s_later

machine E:
    *state s_outer:
        state s_later:
            enter: self._x = True
        ev_ignore:
            assert False and "Can't get here."
        *state s_earlier:
            -> s_later
        ---
        *state s_yup:
            enter: self._y = True
%%
"""


def test_syntax():
    module = utils.compile_state_machine(__file__)
    reactor = smax.SelectReactor()
    #
    A = utils.wrap(module.A)
    a = A(reactor)
    a.start()
    reactor.sync()
    assert a._x == True
    #
    B = utils.wrap(module.B)
    b = B(reactor)
    b.start()
    reactor.sync()
    assert b._x == True
    #
    C = utils.wrap(module.C)
    c = C(reactor)
    c.start()
    reactor.sync()
    assert c._x == True
    #
    D = utils.wrap(module.D)
    d = D(reactor)
    d.start()
    reactor.sync()
    assert d._x == True
    #
    E = utils.wrap(module.E)
    e = E(reactor)
    e.start()
    reactor.sync()
    assert e._x == True
    assert e._y == True
