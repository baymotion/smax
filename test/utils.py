#

import importlib
import os.path
import queue
import smax
import smax.log as log
import types

def compile_state_machine(filename, generated_source_filename="%(dirname)s/.generated.%(basename)s"):
    state_machine_source = smax.load_source(filename)
    machine_spec, python_code = smax.translate(state_machine_source, filename)
    if generated_source_filename:
        dirname, basename = os.path.split(filename)
        out_filename = generated_source_filename % locals()
        with open(out_filename, "wt") as f:
            f.write(python_code)
            f.write('\nr"""\n')
            f.write(state_machine_source)
            f.write('"""\n')
        # this trick lets pudb find the source code.
        module_name = basename.rstrip(".py") + "%04X" % (hash(state_machine_source) & 0xFFFF,)
        module_spec = importlib.util.spec_from_file_location(module_name, out_filename)
        module = importlib.util.module_from_spec(module_spec)
        module_spec.loader.exec_module(module)
    else:
        module = smax.compile_python(python_code)
    return module

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
            s = ".".join(state_name)
            log._debug("%s entering %s" % (self, s))
            self._q.put( (self.ENTERED, s) )
        def _state_machine_exit(self, state_name):
            s = ".".join(state_name)
            log._debug("%s exiting %s" % (self, s))
            self._q.put( (self.EXITED, s) )
        def _state_machine_handle(self, state_name, event_name, *args):
            s = ".".join(state_name)
            log._debug("%s state %s handling %s" % (self, s, event_name))
            self._q.put( (self.HANDLED, s, event_name) )
        def _state_machine_timeout(self, state_name, time_spec):
            s = ".".join(state_name)
            log._debug("%s state %s timed out after %s" % (self, s, time_spec))
            self._q.put( (self.TIMED_OUT, s, time_spec) )
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
                log._trace("Expected %s, got %s." % (e, ev))
                assert ev == e
            try:
                ev = next(i)
                log._debug("Unexpected %s when it should have been empty." % (ev,))
                assert False
            except queue.Empty:
                pass

    return TestFramework
