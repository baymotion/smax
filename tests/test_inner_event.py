# test_inner_event.py

import asyncio
import pytest
import smax
import utils

r"""
%%
machine DirectMachine:
    *state s_a:
        ev_b -> s_b: self.ev_c()
    state s_b:
        pass
    state s_c:
        enter: self.done()
    ev_c -> s_c

machine CallingMachine:
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

    # Direct version calls ev_c directly.
    reactor = smax.SelectReactor()
    module = utils.compile_state_machine(__file__)

    class Direct(utils.wrap(module.DirectMachine)):
        def done(self):
            reactor.stop()

    direct = Direct(reactor)
    direct.start()
    reactor.after_ms(10, direct.ev_b)
    reactor.run()

    # Calling version uses reactor.call to trigger an event.
    class Calling(utils.wrap(module.CallingMachine)):
        def done(self):
            reactor.stop()

    reactor = smax.SelectReactor()
    calling = Calling(reactor)
    calling.start()
    reactor.after_ms(10, calling.ev_b)
    reactor.run()

    # You can run the direct version with an AsyncioReactor.
    loop = asyncio.get_event_loop()
    reactor = smax.AsyncioReactor(loop)
    reactor_task = asyncio.create_task(reactor.run())
    direct = Direct(reactor)
    direct.start()
    await asyncio.sleep(0.1)
    direct.ev_b()
    timeout_s = 10
    await asyncio.wait_for(reactor_task, timeout_s)
