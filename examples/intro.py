# examples/intro.py - Example from the introductory documentation.

import smax
import smax.log as log
import os

r"""
%%
machine MyStateMachine:
    ev_serial_port_lost -> s_no_serial
    *state s_no_serial:
        *state s_idle:
            ev_serial_port(device) -> s_try_open: self._device = device
        state s_try_open:
            [self.open_port(self._device)] -> ^s_serial
            s(1) -> s_try_open
    state s_serial:
        exit: self.close_port()
        *state s_request:
            enter: self.send(b"GO;")
            s(1) -> s_request
            ev_ack -> s_done
        state s_done:
            pass
        ---
        *state s_get_status:
            enter: self.send(b"STATUS;")
            s(5) -> s_get_status
            ev_status(status) -> s_wait_for_status: self.cache_status(status)
        state s_wait_for_status:
            s(5) -> s_get_status
            ev_status(status) -> s_wait_for_status: self.cache_status(status)


machine NotVeryUseful:
    *state s_a:
        ev_x -> s_a_2
    state s_a_2:
        ev_y -> ^s_b_3
    ---
    *state s_b:
        ev_x -> s_b_2
    state s_b_2:
        pass
    state s_b_3:
        pass

%%
"""

# This approach allows observation of all the intermediate
# generated files;
state_machine_source = smax.load_source(__file__)
machine_spec, python_source = smax.translate(state_machine_source, __file__)
with open("/tmp/intro_state_machine.py", "wt") as f:
    f.write('r"""\n%s\n"""\n%s' % (state_machine_source, python_source))
module = smax.compile_python(python_source)
MyStateMachine = module.MyStateMachine
# But this way is easier.
MyStateMachine = smax.load(__file__, "MyStateMachine")
# This way helps debugging: when loaded this way, you can step through
# the generated state machine with e.g. pudb.
def generated_python_python(s):
    with open(".generated_state_machine.py", "wt") as f:
        f.write(s)
smax.load(__file__, "MyStateMachine", save_generated_python=generated_python_python)
import importlib.util
spec = importlib.util.spec_from_file_location("state_machine", ".generated_state_machine.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
MyStateMachine = m.MyStateMachine

class MyDevice(MyStateMachine):
    def __init__(self, reactor):
        super(MyDevice, self).__init__(reactor)
        self._reactor = reactor
    def open_port(self, serial_port_filename):
        try:
            self._fd = os.open(serial_port_filename, os.O_RDWR)
            self._reactor.add_fd(self._fd, self.ready)
            return True
        except FileNotFoundError:
            return False
    def ready(self):
        log.debug("ready")
        s = os.read(self._fd, 65536)
        s = s.decode("utf-8")
        v = s.split("\n")
        for i in v:
            log.debug("i=\"%s\"" % (i,))
            if i == "ACK;":
                self.ev_ack()
                continue
            self.ev_status(i)
    def send(self, message):
        os.write(self._fd, message)
        os.fsync(self._fd)
    def do_more_stuff(self):
        # Super important functionality goes here.
        pass
    def cache_status(self, status):
        log.debug("status=\"%s\"." % (status,))
        self._status = status

def main():
    # Create a runtime environment that drives the state machine
    reactor = smax.SelectReactor()
    # Create the state machine instance itself
    my_device = MyDevice(reactor)
    #my_device._state_machine_debug_enable = True
    # (queue up something to tell the device it's ready)
    reactor.after_s(2, my_device.ev_serial_port, "/dev/tty")
    # Queue up a call to enter all the initial states
    my_device.start()
    # Run the state machine.
    reactor.run()

main()
