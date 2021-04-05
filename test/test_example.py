# test_example.py - Example from the online documentation.

import smax

r"""
%%
machine MyDevice:
    ev_ack -> s_done
    *state s_request:
        enter: self.send(b"GO")
        s(1) -> s_request
    state s_done:
        pass

machine MyStateMachine:
    ev_serial_port_lost -> s_no_serial
    *state s_no_serial:
        *state s_idle:
            ev_serial_port(device) -> s_try_open: self._device = device
        state s_try_open:
            [self.open_port()] -> ^s_serial
            s(1) -> s_try_open
    state s_serial:
        exit: self.close_port()
        *state s_request:
            enter: self.send(b"GO;")
            s(1) -> s_request
            ev_ack -> s_done
        state s_done:
            pass


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

state_machine_source = smax.load_source(__file__)
python_source = smax.translate(state_machine_source, __file__)
module = smax.compile_python(python_source)

class MyDevice(module.MyStateMachine):
    def __init__(self, reactor, serial_port_filename):
        super(MyDevice, self).__init__(reactor)
        self._fd = os.open(serial_port_filename, os.O_RDWR)
    def send(self, message):
        os.write(self._fd, message)
    def do_more_stuff(self):
        # Super important functionality goes here.
        pass

print(python_source)
