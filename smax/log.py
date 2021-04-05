#

import os
import sys
import time
import traceback

start = time.time()

class NoTranscript:
    def write(self, msg):
        pass
    def flush(self):
        pass
transcript=NoTranscript()

def caller(n=0):
    tb = traceback.extract_stack(limit=3+n)
    full_filename, line, method, statement = tb[-(3+n)]
    filename = os.path.basename(full_filename)
    return "%s:%u" % (filename, line)

def write(enable, s):
    transcript.write("%s\n" % s)
    transcript.flush()
    if enable:
        print(s)

enable_trace = False
# enable_trace = True
def trace(msg):
    write(enable_trace, "TRACE %u %.2lf %s -- %s" % (os.getpid(), time.time() - start, caller(), msg))
# _trace is the same as trace except that it reports the caller as the one above who called _trace.
def _trace(msg):
    write(enable_trace, "TRACE %u %.2lf %s -- %s" % (os.getpid(), time.time() - start, caller(1), msg))

enable_debug = True
def debug(msg):
    write(enable_debug, "DEBUG %u %.2lf %s -- %s" % (os.getpid(), time.time() - start, caller(), msg))
# _debug is the same as trace except that it reports the caller as the one above who called _debug.
def _debug(msg):
    write(enable_debug, "DEBUG %u %.2lf %s -- %s" % (os.getpid(), time.time() - start, caller(1), msg))

def error(msg):
    write(True, "ERROR %u %.2lf %s -- %s" % (os.getpid(), time.time() - start, caller(), msg))

# _error is the same as trace except that it reports the caller as the one above who called _error.
def _error(msg):
    write(True, "ERROR %u %.2lf %s -- %s" % (os.getpid(), time.time() - start, caller(1), msg))
