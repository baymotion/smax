# test_debounce.py - Use jinja2 to enable several debounce
# machines.  You could easily instantiate several debouncing
# state machine instances, but using jinja to pull them
# all into a single state machine allows them to all listen
# to common events (which isn't used here).

import asyncio
import jinja2
import pytest
import queue
import smax
from smax import log
import utils

env = jinja2.Environment()

# The debouncer state machine will call your callback
# on the first input change; then ignore subsequent changes
# for {{ignore_time}} (by default, 150ms).  When {{event}}(state)
# is received, we cache the state, then issue ourselves
# an {{update}} event.  This update event then drives the
# callbacks as necessary.
debouncer_template = env.from_string(
    r"""
*state s_debounce_{{name}}:
    {{event}}(active): {{cache}} = active; self.{{update}}()
    *state start:
        {{update}} [{{cache}}] -> s_active
        {{update}} -> s_inactive
    state s_inactive:
        enter: {{inactive}}
        *state s_ignore:
            {{ignore_time}} -> s_listen
        state s_listen:
            [{{cache}}] -> ^s_active
            {{update}} [{{cache}}] -> ^s_active
    state s_active:
        enter: {{active}}
        *state s_ignore:
            {{ignore_time}} -> s_listen
        state s_listen:
            [not {{cache}}] -> ^s_inactive
            {{update}} [not {{cache}}] -> ^s_inactive
"""
)

machine_template = env.from_string(
    r"""
machine TestMachine:
    {{debouncer(name="switch_a")|indent}}
    ---
    {{debouncer(name="switch_b")|indent}}
    ---
    {{debouncer(name="switch_c")|indent}}
"""
)


def debouncer(name, **kwargs):
    default_args = {
        "name": name,
        "ignore_time": "ms(150)",
        "cache": "self._%s_cache" % name,
        "event": "ev_%s" % name,
        "update": "ev_%s_update" % name,
        "active": "self.%s(True)" % name,
        "inactive": "self.%s(False)" % name,
    }
    template_args = {**default_args, **kwargs}  # kwargs replace items in default_args
    global debouncer_template
    return debouncer_template.render(template_args)


@pytest.mark.asyncio
async def test_debounce():
    # In async mode, we can create our reactor anytime.
    loop = asyncio.get_event_loop()
    reactor = smax.AsyncioReactor(loop)
    reactor_task = asyncio.create_task(reactor.run())

    # Render the state machine.
    source = machine_template.render(
        {
            "debouncer": debouncer,
        }
    )
    # Allow some tracing of the jinja output.
    with open(".source", "wt") as f:
        f.write(source)
    spec = smax.parse(source, __file__)
    python_code = smax.generate_python(spec)
    module = smax.compile_python(python_code)

    class Test(utils.wrap(module.TestMachine)):
        def __init__(self, reactor):
            super(Test, self).__init__(reactor)
            self._switch_a = False
            self._switch_b = False
            self._switch_c = False
            self._queue = queue.Queue()

        def switch_a(self, state):
            log.debug("switch_a %s" % state)
            self._queue.put(("a", state))

        def switch_b(self, state):
            log.debug("switch_b %s" % state)
            self._queue.put(("b", state))

        def switch_c(self, state):
            log.debug("switch_c %s" % state)
            self._queue.put(("c", state))

    async def messy_switch(stall_s, cb, state):
        await asyncio.sleep(stall_s)
        for i in range(4):
            cb(state)
            await asyncio.sleep(0.01)
            cb(not state)
            await asyncio.sleep(0.01)
        cb(state)
        # Stay here long enough for the state machine to want to keep it
        await asyncio.sleep(0.2)

    test = Test(reactor)
    test.start()
    reactor.sync()
    await asyncio.gather(
        messy_switch(0.1, test.ev_switch_a, True),
        messy_switch(0.2, test.ev_switch_b, True),
    )
    await asyncio.gather(
        messy_switch(0.1, test.ev_switch_a, False),
        messy_switch(0.2, test.ev_switch_c, True),
    )
    await asyncio.gather(
        messy_switch(0.1, test.ev_switch_b, False),
        messy_switch(0.2, test.ev_switch_c, False),
    )

    reactor.stop()
    await reactor_task

    expected = [
        ("a", True),
        ("b", True),
        ("a", False),
        ("c", True),
        ("b", False),
        ("c", False),
    ]

    for i in expected:
        r = test._queue.get(timeout=0)
        log.trace("r=%s i=%s" % (r, i))
        assert r == i
