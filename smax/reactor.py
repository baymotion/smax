# This file is part of the smax project (http://github.com/baymotion/smax)
# and is copyrighted under GPL v3 or later.

import queue
import time

import smax.log as log


# Reactor framework
class Reactor(object):
    def __init__(self):
        super(Reactor, self).__init__()
        self._q = queue.Queue()
        self._alarms = []
        self._done = False

    # run the reactor until all queued and expired
    # events are done; returns a timeout in seconds
    # until the next event, or None if no alarms are active.
    def sync(self):
        while not self.done():
            if not self._q.empty():
                cb, args = self._q.get()
                log.trace("execute cb=%s." % cb)
                cb(*args)
                continue
            timeout = None
            now = time.time()
            if self._alarms:
                trigger, cb, args = self._alarms[0]
                if trigger <= now:
                    self._alarms.pop(0)
                    log.trace("alarm cb=%s." % cb)
                    cb(*args)
                    continue
                # we've reached our next closest timeout.
                timeout = trigger - now
            return timeout

    def call(self, cb, *args):
        log.trace("queue cb=%s." % cb)
        self._q.put((cb, args))
        self._signal()

    def after_s(self, seconds, callback, *args):
        trigger = time.time() + seconds
        r = (trigger, callback, args)
        log.trace("after_s cb=%s." % callback)
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
        log.trace("stop")
        self._done = True
        self._signal()

    def _signal(self):
        assert False

    def _run_event(self, machine, ev):
        """All events are queued up."""
        self.call(ev, machine)
