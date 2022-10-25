# This file is part of the smax project (http://github.com/baymotion/smax)
# and is copyrighted under GPL v3 or later.

import os
import select
import smax

import smax.log as log


class SelectReactor(smax.Reactor):
    """
    Reactor that works with unix's select so that the entire application
    works in a single thread.  Use add_fd and remove_fd to trigger
    a callback when select() returns data ready on the file descriptor.
    """

    update = b"U"

    def __init__(self):
        self._control_read, self._control_write = os.pipe()
        self._r = {self._control_read: self.__control_ready}
        self._w = {}
        self._x = {}
        super(SelectReactor, self).__init__()

    def run(self):
        while True:
            timeout = self.sync()
            if self.done():
                return
            # timeout may be None
            log.trace("timeout=%s." % timeout)
            r, w, x = self.select(timeout)
            for ir in r:
                self._r[ir]()
            for iw in w:
                self._w[iw]()
            for ix in x:
                self._x[ix]()

    def select(self, timeout):
        """Allow subclasses to modify our blocking behavior."""
        r, w, x = select.select(self._r.keys(), self._w.keys(), self._x.keys(), timeout)
        return r, w, x

    def _signal(self):
        os.write(self._control_write, self.update)

    def add_fd(self, fd, read_callback):
        self._r[fd] = read_callback
        self._signal()

    def remove_fd(self, fd):
        del self._r[fd]
        self._signal()

    def __control_ready(self):
        # Get 'update' out of the ingress port.
        os.read(self._control_read, 4096)
