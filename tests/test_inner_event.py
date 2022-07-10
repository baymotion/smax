# test_inner_event.py

import asyncio
import pytest
import smax
import utils

r"""
%%
machine BadMachine:
    *state s_a:
        ev_b -> s_b: self.ev_c()
    state s_b:
        pass
    state s_c:
        enter: self.done()
    ev_c -> s_c

machine GoodMachine:
    *state s_a:
        ev_b -> s_b: self.call(self.ev_c)
    state s_b:
        pass
    state s_c:
        enter: self.done()
    ev_c -> s_c
%%
"""


@pytest.mark.asyncio
async def test_inner_event():

    # Bad version: This triggers a RuntimeError.
    reactor = smax.SelectReactor()
    module = utils.compile_state_machine(__file__)

    class Bad(utils.wrap(module.BadMachine)):
        def done(self):
            reactor.stop()

    bad = Bad(reactor)
    bad.start()
    try:
        reactor.after_ms(10, bad.ev_b())
        reactor.run()
    except RuntimeError as e:
        pass
    else:
        assert False

    # Good version: This uses SelectReactor in the right way.
    class Good(utils.wrap(module.GoodMachine)):
        def done(self):
            reactor.stop()

    reactor = smax.SelectReactor()
    good = Good(reactor)
    good.start()
    reactor.after_ms(10, good.ev_b())
    reactor.run()

    # You can run the bad version with an AsyncioReactor.
    loop = asyncio.get_event_loop()
    reactor = smax.AsyncioReactor(loop)
    reactor_task = asyncio.create_task(reactor.run())
    bad = Bad(reactor)
    bad.start()
    await asyncio.sleep(0.1)
    bad.ev_b()
    timeout_s = 10
    await asyncio.wait_for(reactor_task, timeout_s)
