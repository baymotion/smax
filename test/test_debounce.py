# test_debounce.py - Use jinja2 to enable several debounce
# machines.

import jinja2
import smax
from smax import log
import sys
import utils

env = jinja2.Environment()

debouncer_template=env.from_string(r"""
*state s_debounce_{{name}}:
    ev_{{name}}(active): self._{{name}}_active = active
    *state start:
        [self._{{name}}_active] -> s_active
        -> s_inactive
    state s_inactive:
        enter: {{inactive}}
        *state s_ignore:
            {{ignore_time}} -> s_listen
        state s_listen:
            [self._{{name}}_active] -> ^s_active
            ev_{{name}}(active) [active] -> ^s_active: self._{{name}}_active = active
            ev_{{name}}(active): self._{{name}}_active = active
    state s_active:
        enter: {{active}}
        *state s_ignore:
            {{ignore_time}} -> s_listen
        state s_listen:
            [not self._{{name}}_active] -> ^s_inactive
            ev_{{name}}(active) [not active] -> ^s_inactive: self._{{name}}_active = active
            ev_{{name}}(active): self._{{name}}_active = active
""")

machine_template=env.from_string(r"""
import smax.log as log
machine TestMachine:
    {{debouncer(
        name="switch_a",
        inactive="self.switch_a_inactive()",
        active="self.switch_a_active()",
    )|indent}}
    ---
    {{debouncer(
        name="switch_b",
        inactive="self.switch_b_inactive()",
        active="self.switch_b_active()",
    )|indent}}
    ---
    {{debouncer(
        name="switch_c",
        inactive="self.switch_c_inactive()",
        active="self.switch_c_active()",
    )|indent}}
""")

def test_debounce():
    source = machine_template.render({
        "debouncer": lambda **kwargs: debouncer_template.render(kwargs),
    })
    # Allow some tracing of the jinja output.
    with open(".source", "wt") as f:
        f.write(source)
    spec = smax.parse(source, __file__)
    python_code = smax.generate_python(spec)
    module = smax.compile_python(python_code)
    class Test(utils.wrap(module.TestMachine)):
        def __init__(self, reactor):
            super(Test, self).__init__(reactor)
            self._switch_a_active = False
            self._switch_b_active = False
            self._switch_c_active = False
        def switch_a_active(self):
            log.debug("switch_a_active")
        def switch_a_inactive(self):
            log.debug("switch_a_inactive")
        def switch_b_active(self):
            log.debug("switch_b_active")
        def switch_b_inactive(self):
            log.debug("switch_b_inactive")
        def switch_c_active(self):
            log.debug("switch_c_active")
        def switch_c_inactive(self):
            log.debug("switch_c_inactive")
    reactor = smax.SelectReactor()
    test = Test(reactor)
    test.start()
    test.ev_switch_a(False)
    test.ev_switch_a(True)
    """
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
    """
