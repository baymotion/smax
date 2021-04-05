#

import queue
import time

import smax.log as log

# Reactor framework
class Reactor(object):
    def __init__(self):
        super(Reactor, self).__init__()
        self._q = queue.Queue()
        self._alarms = [ ]
        self._done = False
    # run the reactor until all queued and expired
    # events are done; returns a timeout in seconds
    # until the next event, or None if no alarms are active.
    def sync(self):
        while not self.done():
            if not self._q.empty():
                cb = self._q.get()
                log.trace("q cb=%s." % cb)
                cb()
                continue
            timeout = None
            now = time.time()
            if self._alarms:
                a = self._alarms[0]
                trigger, cb = a
                if trigger <= now:
                    self._alarms.pop(0)
                    log.trace("alarm cb=%s." % cb)
                    cb()
                    continue
                # we've reached our next closest timeout.
                timeout = trigger - now
            return timeout
    def call(self, cb, *args):
        self._q.put(lambda: cb(*args))
        self._signal()
    def after_s(self, seconds, callback, *args):
        trigger = time.time() + seconds
        r = (trigger, lambda: callback(*args))
        self._alarms.append(r)
        self._alarms.sort()
        self._signal()
        return r
    def after_ms(self, ms, callback, *args):
        return self.after_s(ms / 1000.0, callback, *args)
    def cancel_after(self, r):
        if r not in self._alarms:
            return
        self._alarms.remove(r)
        self._signal()
    def done(self):
        return self._done
    def stop(self):
        self._done = True
        self._signal()
    def _signal(self):
        assert False

