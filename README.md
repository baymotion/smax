# Overview

Smax, pronounced "smash," is a DSL for implementing Harel state machines with a python3 back end.

Smax translates a state machine specification into python code which you can import, subclass, and execute.  The state machine specification is usually given between special tags in the python module that uses it; but the specification can come from a literal string or an input file.

One useful definition of an object state pattern is that the object's methods behave differently depending on previous calls to that object.  Ordinary python code only allows you one definition of a method, meaning that you have to check your state inside that method.  Using smax, you provide multiple definitions of a method, and the state you're currently in decides which definition to use.

Smax allows you to change your state on elapsed time as well as received events.

## Features

  * Straightforward input script
  * Python 3 generated code
  * Very complex program behavior is easy to manage
  * Tiny runtime can be easily adapted, if it's not already supported
  * Generated code is pretty efficient
  * Transitions can be based on timers
  * Both the source and generated code work nicely with diff and version
    control tools

# Examples

## A simple single-level state machine

For a simple example, let's consider a device that's controlled by, say, a serial port.  Because serial ports don't guarantee delivery, we'll retry sending a command until we get an acknowledgement from the device.

    machine MyStateMachine:
        *state s_request:
            enter: self.send(b"GO;")
            s(1) -> s_request
            ev_ack -> s_done
        state s_done:
            pass

Some notes:

  * Like python, indentation is used to describe the stucture of a machine.  All the states of MyStateMachine are indented from the machine declaration, the clauses and transitions specific to a state are all indented within the declaration of the state.

  * There are two states, **s_request** and **s_done**.  By convention, name all states with an **s_** prefix; all state names must be valid python identifiers.

  * States can have "enter:" and "exit:" clauses providing code which will be executed when transitioning into or out of the state.  Code can be specified on the same line as "enter:" or "exit:" (as above); multi-line code can be given by indenting on the following line:

        *state s_request:
            enter:
                self.send(b"GO;")
                self.do_more_stuff()
            s(1) -> s_request

    The convention is to keep code in the state machine specification to a minimum; usually just a single method call.  Putting more than a few lines of code in the state machine clauses can hide the structure--and there are a lot of places you can attach code.  It's better to have the state machine call a method which does what you want, and implement that callback in a subclass or superclass.

  * **s_request** is the _default_ state, indicated by the **\*** in front of the reserved word **state**.  Unless otherwise requested, starting the state machine will always enter this state, executing the code in its enter clause.

  * **s(1) -> s_request** is a _timed_ transition.  If we enter this state, and don't execute another transition within 1 second, we'll exit **s_request**, enter **s_request** again, and execute the code in its enter clause again.  Any other transition will cause the timed transition to be forgotten.  In the absence of an **ev_ack**, this loop  will go on forever.  **s(n)** is used to indicate a timeout in terms of seconds; **ms(n)** is also available to specify timeouts in milliseconds.  Floating point values are allowed in both cases; timeouts do not need to be constant values, and will be evaluated at the time the state is entered.

  * This state machine has one event, **ev_ack**.  The generated state machine will have an **ev_ack** method, which does nothing unless you're in the **s_request** state, in which case it causes the state machine to exit **s_request** and enter **s_done**.

  * **s_done** has no transitions, so once the state machine gets here, it'll stay forever.

Most commonly, the state machine is presented within "%%" marks in the same python file where the state machine is used.  Put that within r"""...""" so the python interpreter ignores it.

    # Python code
    r"""
    %%
    machine MyStateMachine:
        ...
    %%
    """

Smax has a "load_source" method that reads the input file, filtering all lines not inside the "%%" sections.  There can be many of these sections in a given input file.

Smax will translate the state machine specification and generate an implementation class called MyStateMachine, named per the **machine** statement.  Here is an excerpt from the generated code:

    class MyStateMachine(object):
        def __init__(self, reactor):
            ...
        def start(self):
            ...
        def end(self):
            ...
        def ev_ack(self):
            ...

By convention, application code subclasses MyStateMachine and the subclass provides the methods that MyStateMachine will call:

    class MyDevice(MyStateMachine):
        def __init__(self, reactor, serial_port_filename):
            super(MyDevice, self).__init__(reactor)
            self._fd = os.open(serial_port_filename, os.O_RDWR)
        def send(self, message):
            os.write(self._fd, message)
        def do_more_stuff(self):
            # Super important functionality goes here.
            pass

Now let's discuss how ev_ack is called.

A Reactor instance provides the runtime support for timing and callback queues that the state machine uses to update itself.  To run the state machine, instantiate a reactor, instantiate your object, and run it.  A single reactor instance can handle any number of state machines.

    def main():
        reactor = smax.SelectReactor()
        my_device = MyDevice(reactor, "/dev/ttyS0")
        my_device.start()
        reactor.run()

### Reactor

A reactor provides the runtime environment for state machines.  Specifically,

- The call to reactor.run() goes into a perpetual loop, blocking until an event is observed.  When it sees an event, it calls an event handler registered with that event.  You can call reactor.stop() to cause reactor.run() to terminate.
- All handlers executed by the reactor run in the same thread sequentially.  If that is the only thread in your program, then you don't need any locking.
- If you have other threads, you can call reactor.call(cb) to schedule the reactor to call cb() at the next opportunity.  cb() will run in the reactor thread.
- All handlers should be non blocking: the reactor won't wait for the next event until the current handler returns.  If your reactor stops working, it's probably because your handler is blocking on something.

Reactor is an abstract class.  smax provides two useful implementations: SelectReactor and PyQtReactor.

- SelectReactor has add_fd(fd, callback) and remove_fd(fd) methods and waits on file descriptors.
- PyQtReactor integrates with PyQt4 so that its callbacks all run in the same thread as PyQt.  The means your state machine can directly read or modify the state of the UI safely.  PyQtReactor has add_fd(fd, callback) and remove_fd(fd) just like SelectReactor does.
- reactor.after_s(seconds, cb, *cb_args) and reactor.after_ms(ms, cb, *cb_args) schedule callbacks that will execute after the given amount of time has elapsed--this is how s() and ms() work.  Both methods return an object which can be used with reactor.cancel_after() to remove a callback from the alarm list.  It is always ok to cancel an alarm, even after it has executed.

Sending events to your state machine is almost always done by calling the appropriate method in a reactor callback.  State machine event methods all work by queuing themselves (with calls to reactor.call()), so events can be posted to a state machine from any thread.

Going back to our example, let's show how ev_ack should be called.  We'll use select_reactor to get a callback when serial port data is ready:

```
class MyDevice(MyStateMachine):
...
	def start(self)
        super(MyDevice, self).start()
		reactor.add_fd(self._fd, self.data_ready)
    def data_ready(self):
        """Called when data is available on the serial port."""
        data = os.read(self._fd, 65536)
        if data == b"ACK;":
            self.ev_ack()
```

## More complicated state machines

The above example assumes that the call to self.send() is always available-- but I happen to be working with equipment that is connected by a USB to RS232 adapter.  This creates a few new requirements:

  * The USB adapter can be disconnected--don't send data when the device disappears.
  * Linux's udev can report the presence of the USB device several seconds before an open to the device will succeed, so retries on the open are required after the USB device is found.

Here's one way to accommodate these new requirements:

    machine MyStateMachine:
        ev_serial_port_lost -> s_serial_absent
        *state s_serial_absent:
            *state s_idle:
                ev_serial_port_found(device) -> s_try_open:
                    self._device = device
            state s_try_open:
                [self.open_port()] -> ^s_serial_present
                s(1) -> s_try_open
        state s_serial_present:
            exit: self.close_port()
            *state s_request:
                enter: self.send(b"GO;")
                s(1) -> s_request
                ev_ack -> s_done
            state s_done:
                pass

Notes:

  * New events: **ev_serial_port_lost** is called when the USB port becomes disconnected, and **ev_serial_port_found** is called when the USB port is found.  On Linux, these are callbacks from udev.

  * **s_serial_absent** and **s_serial_present** have _inner state machines_.  By default, an entry to **s_serial_absent** results in an entry to **s_serial_absent.s_idle** too.  If you're in **s_request** or **s_done**, you are also in **s_serial_present**.  (You can have states of the same names in different parent classes; they are treated entirely independently.)  Inner state machines work exactly the same way outer ones do, except that events that are handled in inner states will preclude handling of that same event in the encompassing state, much the same way overriding a method in a subclass completely replaces a superclass method.

  * **ev_serial_port_lost** causes a transition to **s_serial_absent** regardless of where you are in the state machine, calling the exit clauses for all the states that the machine is currently in.

  * **ev_serial_port_found** accepts a parameter (device), queues a transition to **s_try_open**, and has a code clause following the :.  The parameter (device) is presented as a local variable to the code clause when it executes, the same way a conventional method accesses its parameters.  The transition code executes after exiting **s_idle** and before entering **s_try_open**.  Calls to **ev_serial_port_found** are completely ignored unless you are in **s_serial_absent.s_idle**.  (You can always add ev_serial_port_found handling to other states.)

  * States can have default transitions.  Without an event name, the transition will be queued immediately when the state is entered.

        *state s_first:
            enter: print("Entering s_first")
            exit: print("Leaving s_first")
            -> s_next: print("Moving to s_next")
        state s_next:
            enter: print("Entering s_next")

    This results in this output:

        Entering s_first
        Leaving s_first
        Moving to s_next
        Entering s_next

  * Transitions can have conditions, indicated by a condition in brackets.  When an event is called, if the code inside the brackets evalutes to False, then the transition is ignored:

        *state s_one:
            ev_event [self.condition_a()] -> s_two
            ev_event [self.condition_b()] -> s_three
            ev_event -> s_four
        state s_two:
            pass

    For a single call to ev_event when in s_one, each condition will be evaluated in the order given in the script.  The first one that returns True will be followed and the rest will not be checked.  In this example, we'll always wind up in either s_two, s_three, or s_four, assuming that we're in s_one.  The statement "ev_event -> s_four" is considered to have a condition that is always True.

    In the above example, a default transition is combined with a condition:

            state s_try_open:
                [self.open_port()] -> ^s_serial_present
                s(1) -> s_try_open

    This results in a call to self.open_port(), which will repeat every second as long as open_port() returns False.  Because **s_serial_present** is in the state machine _above_ **s_try_open**, a caret (^) tells smax to look in the encompassing state machine for the target state.  You can transition to a specific substate in another state machine-- the **^s_serial** is exactly the same as **^s_serial.s_request** (given that **s_request** is where it would go to anyway).

## Parallel state machines

Lets add another requirement, which is to cache a status value.  Our example equipment will send us a status message when things change; we can ask it to send the latest status now by sending the "STATUS" command.  In this example, we'll ask for the status when we start and any time we haven't received a status update in 5 seconds.

    machine MyStateMachine:
        ...
        state s_serial_present:
            exit: self.close_port()
            *state s_request:
                enter: self.send(b"GO;")
                s(1) -> s_request
                ev_ack -> s_done
            state s_done:
                pass
            ---
            *state s_get_status:
                enter: self.send(b"STATUS;")
                s(5) -> s_get_status
                ev_status(status) -> s_wait_for_status: self.cache_status(status)
            state s_wait_for_status:
                s(5) -> s_get_status
                ev_status(status) -> s_wait_for_status: self.cache_status(status)

Notes:
  * The "---" notation separates parallel state machines; there can be any number of parallel state machines.  When this machine starts, we will be in both **s_get_status** and **s_request** states.  Loss of communication (via ev_serial_port_lost) causes both state machines to terminate cleanly.
  * Entering the parent state will, by default, enter the default states of all inner state machines.  In this example, the default entry to **s_serial** puts you in both **s_request** and **s_get_status**.

Additional parallel state machine notes:

  * Parallel state machines at the top level too:

        machine NotVeryUseful:
            *state s_a:
                ev_x -> s_a_2
            state s_a_2:
                ev_y -> ^s_b_3
            ---
            *state s_b:
                ev_x -> s_b_2
            state s_b_2:
                pass
            state s_b_3:
                pass

  * Events are observed by all active parallel states.  In this example, just after starting, both **s_a** and **s_b** will respond when **ev_x** is called.

  * An event can transition to the inner state of another parallel state machine.  In this case, all the rest of the parallel states, including the one requesting the transition, will exit, then enter default states.  In the above example, calling **ev_y** in **s_a_2** will result in exiting **s_a_2** and **s_b_2**, and entering **s_a** and **s_b_3**.

# API

## Reactor -- the state machine runtime.

State machines keep track of the states they're in and use reactors to queue up the methods they need to execute.  If you supply your own reactor instance, the compiled state machine code will require no other external runtime support.   State machines will call these methods on a reactor:

    class Reactor:
        # Add a callback with arguments to the queue.
        def call(self, cb, *args):
            ...
        # Add a callback which will be queued after the
        # given number of seconds have elapsed.  Returns
        # a handle which will be passed to cancel_after.
        def after_s(self, seconds, callback, *args):
            ...
        # Same as after_s except that the time
        # is specified in milliseconds.
        def after_ms(self, ms, callback, *args):
            ...
        # Given a handle returned by after_s or
        # after_ms, cancel that timeout.  State machines
        # always cancel all their callbacks-- it
        # must be ok to cancel timers that have already
        # expired.
        def cancel_after(self, r):
            ...

Smax provides some additional methods that your program can call:

    class Reactor: # Continued...
        # Call all the callbacks currently queued, including
        # all those whose timeouts have expired.  If there are
        # any timeouts that haven't expired yet, this method
        # returns the number of seconds (floating point) until
        # the next timeout expires; if there are no timeouts,
        # then returns None.
        def sync(self):
            ...

