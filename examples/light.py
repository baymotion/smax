# examples/light.py

# Traffic light state machine example.

import smax
import os

r"""
%%

machine LightMachine:
    *state s_stop:
        enter: self.red(True)
        exit: self.red(False)
        s(5) -> s_go
    state s_go:
        enter: self.green(True)
        exit: self.green(False)
        s(5) -> s_warn
    state s_warn:
        enter: self.yellow(True)
        exit: self.yellow(False)
        s(1) -> s_stop
%%
"""

# You can observe the intermediate stages by looking
# at values returned here
light_machine_source = smax.load_source(__file__)
light_machine_spec, light_machine_python = smax.translate(light_machine_source, __file__)
light_machine_module = smax.compile_python(light_machine_python)
LightMachine = light_machine_module.LightMachine
# Or you can do it in one step.
LightMachine = smax.load(__file__, "LightMachine")

class Light(LightMachine):
    def __init__(self, q):
        super(Light, self).__init__(q)
        self.red(False)
        self.yellow(False)
        self.green(False)
    def red(self, status):
        print("red: %s" % ("on" if status else "off"))
    def yellow(self, status):
        print("yellow: %s" % ("on" if status else "off"))
    def green(self, status):
        print("green: %s" % ("on" if status else "off"))

def main():
    reactor = smax.SelectReactor()
    light = Light(reactor)
    light.start()
    reactor.run()

if __name__=="__main__":
    main()

