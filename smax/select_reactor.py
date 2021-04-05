#


import os
import queue
import select
import smax
import time

import smax.log as log

# Reactor that works with unix's select so that the entire application
# works in a single thread.  Use add_fd and remove_fd to trigger
# a callback when select() returns data ready on the file descriptor.
class SelectReactor(smax.Reactor):
    update = b'U'
    def __init__(self):
        self._control_read, self._control_write = os.pipe()
        self._r = { self._control_read: self.__control_ready }
        self._w = { }
        self._x = { }
        super(SelectReactor, self).__init__()
    def run(self):
        while True:
            timeout = self.sync()
            if self.done():
                return
            # timeout may be None
            log.trace("timeout=%s." % timeout)
            r, w, x = select.select(self._r.keys(), self._w.keys(), self._x.keys(), timeout)
            for ir in r:
                self._r[ir]()
            for iw in w:
                self._w[iw]()
            for ix in x:
                self._x[ix]()
    def _signal(self):
        os.write(self._control_write, self.update)
    def add_fd(self, fd, read_callback):
        self._r[fd] = read_callback
        self._signal()
    def remove_fd(self, fd):
        del self._r[fd]
        self._signal()
    def __control_ready(self):
        msg = os.read(self._control_read, 4096)

