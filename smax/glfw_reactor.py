#

import glfw
import os
import smax
import threading


class GlfwReactor(smax.SelectReactor):
    """Provide a reactor that works well with glfw;
    this works by creating a background thread that
    runs only when we're blocking on our select,
    and synchronizing that background select call
    so that it calls glfw.post_empty_event()
    """

    def __init__(self):
        super(GlfwReactor, self).__init__()
        self._rp, self._wp = os.pipe()
        self._rq, self._wq = os.pipe()
        self._thread = threading.Thread(target=self._background)
        self._thread.setDaemon(True)
        self._thread.start()

    def _background(self):
        while True:
            # Stay here until bg should check
            assert os.read(self._rp, 256) == b"X"
            # Block until something is ready (which could be _signal)
            super(GlfwReactor, self).select(None)
            # Wake up the foreground thread
            glfw.post_empty_event()
            # Let it know we're done
            os.write(self._wq, b"Y")

    def select(self, timeout):
        # tell bg to check
        os.write(self._wp, b"X")
        # allow glfw to do its stuff
        self.glfw_wait(timeout)
        # wake bg up from it's select call
        self._signal()
        # wait for it to get past post_empty_event
        assert os.read(self._rq, 256) == b"Y"
        # now handle all the active events
        return super(GlfwReactor, self).select(timeout)

    def glfw_wait(self, timeout):
        if timeout is None:
            glfw.wait_events()
        else:
            glfw.wait_events_timeout(timeout)
