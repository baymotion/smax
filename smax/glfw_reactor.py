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
    wake up the foreground thread.  Note that we
    queue up all event calls to the reactor, this
    is so that they can be called within the glfw
    callback without needing to manually bump the
    background out of the select call.
    """

    RESUME = b"resume"
    DONE = b"done"
    TERMINATE = b"terminate"
    TERMINATED = b"terminated"

    def __init__(self):
        super(GlfwReactor, self).__init__()
        self._rp, self._wp = os.pipe()
        self._rq, self._wq = os.pipe()

    def _background(self):
        while True:
            # Stay here until bg should check
            c = os.read(self._rp, 256)
            if c == self.TERMINATE:
                break
            assert c == self.RESUME
            # Block until something is ready (which could be _signal)
            super(GlfwReactor, self).select(None)
            # Wake up the foreground thread
            glfw.post_empty_event()
            # Let it know we're done
            os.write(self._wq, self.DONE)
        os.write(self._wq, self.TERMINATED)

    def select(self, timeout):
        # tell bg to check
        os.write(self._wp, self.RESUME)
        # allow glfw to do its stuff
        self.glfw_wait(timeout)
        # wake bg up from it's select call
        self._signal()
        # wait for it to get past post_empty_event
        r = os.read(self._rq, 256)
        assert r == self.DONE
        # now handle all the active events
        return super(GlfwReactor, self).select(timeout)

    def run(self):
        thread = threading.Thread(target=self._background)
        thread.setDaemon(True)
        thread.start()
        super(GlfwReactor, self).run()
        os.write(self._wp, self.TERMINATE)
        assert os.read(self._rq, 256) == self.TERMINATED

    def glfw_wait(self, timeout):
        if timeout is None:
            glfw.wait_events()
        else:
            glfw.wait_events_timeout(timeout)
