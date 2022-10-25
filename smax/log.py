# This file is part of the smax project (http://github.com/baymotion/smax)
# and is copyrighted under GPL v3 or later.

import os
import time
import traceback

start = time.time()


class NoTranscript:
    def write(self, msg):
        pass

    def flush(self):
        pass


transcript = NoTranscript()
enable_trace = False
enable_debug = True


def caller(n=0):
    tb = traceback.extract_stack(limit=3 + n)
    full_filename, line, method, statement = tb[-(3 + n)]
    filename = os.path.basename(full_filename)
    return "%s:%u" % (filename, line)


def write(enable, s):
    transcript.write("%s\n" % s)
    transcript.flush()
    if enable:
        print(s)


def trace(msg):
    write(
        enable_trace,
        "TRACE %u %.2lf %s -- %s"
        % (
            os.getpid(),
            time.time() - start,
            caller(),
            msg,
        ),
    )


def _trace(msg):
    """
    _trace is the same as trace except that it reports
    the caller as the one above who called _trace.
    """
    write(
        enable_trace,
        "TRACE %u %.2lf %s -- %s"
        % (
            os.getpid(),
            time.time() - start,
            caller(1),
            msg,
        ),
    )


def debug(msg):
    write(
        enable_debug,
        "DEBUG %u %.2lf %s -- %s"
        % (
            os.getpid(),
            time.time() - start,
            caller(),
            msg,
        ),
    )


def _debug(msg):
    """
    _debug is the same as trace except that it reports
    the caller as the one above who called _debug.
    """
    write(
        enable_debug,
        "DEBUG %u %.2lf %s -- %s"
        % (
            os.getpid(),
            time.time() - start,
            caller(1),
            msg,
        ),
    )


def error(msg):
    write(
        True,
        "ERROR %u %.2lf %s -- %s"
        % (
            os.getpid(),
            time.time() - start,
            caller(),
            msg,
        ),
    )


def _error(msg):
    """
    _error is the same as trace except that it reports the caller as the one
    above who called _error.
    """
    write(
        True,
        "ERROR %u %.2lf %s -- %s" % (os.getpid(), time.time() - start, caller(1), msg),
    )
