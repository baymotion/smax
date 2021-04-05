#

import queue
import smax
import smax.log as log
import types

def compile_state_machine(filename, generated_source_filename="generated_state_machine.py"):
    state_machine_source = smax.load_source(filename)
    python_code = smax.translate(state_machine_source, filename)
    if generated_source_filename:
        with open(generated_source_filename, "wt") as f:
            f.write(python_code)
            f.write('r"""\n')
            f.write(state_machine_source)
            f.write('"""\n')
    # Create the module we're return with
    m = types.ModuleType("state_machine")
    exec(python_code, m.__dict__)
    return m

def wrap(state_machine_class):
    """
        Returns a class that
        - inherits from state_machine_class
        - hooks into the debugging facilities
            of the state machine class in order
            to instrument the state machine
            behavior.
        - provides "expected" to test for the
            list of expected events and actions.
    """
    class TestFramework(state_machine_class):
        ENTERED = "entered"
        EXITED = "exited"
        HANDLED = "handled"
        IGNORED = "ignored"
        TIMED_OUT = "timed-out"
        def __init__(self, reactor):
            super(TestFramework, self).__init__(reactor)
            self._started = False
            self._done = False
            self._q = queue.Queue()
        def _state_machine_debug(self, msg):
            log._trace("%s %s (state=%s)" % (self, msg, self._state.keys()))
        def _state_machine_enter(self, state_name):
            log._debug("%s entering %s" % (self, state_name))
            self._q.put( (self.ENTERED, state_name) )
        def _state_machine_exit(self, state_name):
            log._debug("%s exiting %s" % (self, state_name))
            self._q.put( (self.EXITED, state_name) )
        def _state_machine_handle(self, state_name, event_name, *args):
            log._debug("%s state %s handling %s" % (self, state_name, event_name))
            self._q.put( (self.HANDLED, state_name, event_name) )
        def _state_machine_timeout(self, state_name, time_spec):
            log._debug("%s state %s timed out after %s" % (self, state_name, time_spec))
            self._q.put( (self.TIMED_OUT, state_name, time_spec) )
        def _state_machine_ignored(self, event_name, *args):
            log._debug("%s ignored %s" % (self, event_name))
            self._q.put( (self.IGNORED, event_name) )
        def __repr__(self):
            return "%s@0x%X" % (type(self).__name__, id(self))
        # Returns an iterator that fetches the sequence of 
        # currently buffered enter/exit/handle/ignored call.
        def events(self):
            while True:
                x = self._q.get(timeout=0)
                yield x
        # Compares the list of currently buffered calls
        # against the expected list.  If any item is
        # different, or the lengths are different,
        # an assert failure occurs.
        def expected(self, event_list):
            i = self.events()
            for e in event_list:
                ev = next(i)
                log._debug("Expected %s, got %s." % (e, ev))
                assert ev == e
            try:
                ev = next(i)
                log._debug("Unexpected %s when it should have been empty." % (ev,))
                assert False
            except queue.Empty:
                pass

    return TestFramework
