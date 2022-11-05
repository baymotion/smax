#

import glfw
import os
import smax
import smax.log as log
import threading


class GlfwReactor(smax.SelectReactor):
    """Provide a reactor that works well with glfw;
    this works by creating a background thread that
    runs only when we're blocking on our select,
    and synchronizing that background select call
    so that it calls glfw.post_empty_event() to
    wake up the foreground thread.
    """

    BG_RUN = b"bg_run"  # fg tells bg to run select()
    FG_ACK = b"fg_ack"  # fg tells bg that it woke up
    BG_IDLE = b"bg_idle"  # bg tells fg that it's out of select
    BG_TERMINATE = b"bg_terminate"  # fg tells bg to exit
    BG_TERMINATED = b"bg_terminated"  # bg tells fg that it exited

    def __init__(self):
        super(GlfwReactor, self).__init__()
        self._rp, self._wp = os.pipe()  # fg writes BG_RUN or BG_TERMINATE
        self._rq, self._wq = os.pipe()  # fg writes FG_ACK
        # add a handler for rq that won't be used;
        # we just use this so the superclass' select
        # call will wake up when the foreground flags
        # us (via write to wq).  _rq and _rp are separated
        # so we guarantee distinct reads of BG_RUN and FG_ACK.
        self.add_fd(
            self._rq,
            lambda: log.trace("_rq callback read=%s" % (os.read(self._rq, 256),)),
        )
        self._rr, self._wr = os.pipe()  # bg writes BG_IDLE or BG_TERMINATED

    def _background(self):
        just_fg = [self._rq]
        while True:
            # Stay here until bg should check
            c = os.read(self._rp, 256)
            if c == self.BG_TERMINATE:
                break
            assert c == self.BG_RUN
            # Block until the state machine has something to do
            r, w, x = super(GlfwReactor, self).select(None)
            # Does fg want us to go idle again?
            if r != just_fg:
                # We found something in our select that needs attention,
                # so wake up the foreground thread.  If it was
                # just [self._rq] then the foreground already woke
                # up and is waiting for us.
                glfw.post_empty_event()
            # Wait for it to wake up
            r = os.read(self._rq, 256)
            assert r == self.FG_ACK
            # Let fg know we got it
            os.write(self._wr, self.BG_IDLE)
            # Now go back to sleep again.
            continue
        # (we received BG_TERMINATE)
        os.write(self._wr, self.BG_TERMINATED)

    def select(self, timeout):
        # tell bg to start checking select
        os.write(self._wp, self.BG_RUN)
        # allow glfw to do its stuff
        self.glfw_wait(timeout)
        # Let bg know we woke up
        os.write(self._wq, self.FG_ACK)
        # Wait for it to go back to sleep
        r = os.read(self._rr, 256)
        assert r == self.BG_IDLE
        # Now handle all our state machine stuff
        return super(GlfwReactor, self).select(0)

    def run(self):
        thread = threading.Thread(target=self._background)
        thread.setDaemon(True)
        thread.start()
        super(GlfwReactor, self).run()
        # Even though bg is daemon, let's shut it down cleanly.
        os.write(self._wp, self.BG_TERMINATE)
        r = os.read(self._rr, 256)
        assert r == self.BG_TERMINATED

    def glfw_wait(self, timeout):
        if timeout is None:
            glfw.wait_events()
        else:
            glfw.wait_events_timeout(timeout)
