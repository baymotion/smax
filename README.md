# Overview

Smax, pronounced "smash," is a DSL for implementing Harel (heirarchical) state machines with a python3 back end.

Smax translates a state machine specification into python code which you can import, subclass, and execute.  The state machine specification is usually given between special tags in the python module that uses it; but the specification can come from a literal string or an input file.

One useful definition of an object state pattern is that the object's methods behave differently depending on previous calls to that object.  Ordinary python code only allows you one definition of a method, meaning that you have to check your state inside that method.  Using smax, you provide multiple definitions of a method (which we'll call events) and the state you're currently in decides which definition to use.

Smax allows you to change your state on elapsed time as well as received events.

## Features

  * Straightforward input script
  * Python 3 generated code
  * Very complex program behavior is easy to manage
  * Tiny runtime can be easily adapted, if it's not already supported
  * Generated code is pretty efficient
  * Transitions can be based on timers
  * Both the source and generated code work nicely with diff and version control tools
  * AsyncioReactor supports state machine execution under asyncio
  * State machine specifications can be dumped to yaml or plantuml

# Installation

    pip3 install smax-dsl

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

  * This example has two states, **s_request** and **s_done**.  By convention, name all states with an **s_** prefix; all state names must be valid python identifiers.

  * States have optional "enter:" and "exit:" clauses.  These provide code which will be executed when transitioning into or out of the state.  Code can be specified on the same line as "enter:" or "exit:" (as above); multiple lines of code can be given by indenting on the following line:

        *state s_request:
            enter:
                self.send(b"GO;")
                self.do_more_stuff()
            s(1) -> s_request

    Best practice is to keep code in the state machine specification to a minimum, usually just a call to a method which you'll implement elsewhere (e.g. subclass or superclass).  Putting more than a few lines of code in the state machine clauses will hide the machine structure--and there are a lot of places you can attach code.  It's better to have the state machine call a method which does what you want, and implement that callback elsewhere.

  * **s_request** is the _default_ state, indicated by the **\*** in front of the reserved word **state**.  Unless otherwise requested, starting the state machine will always enter this state, executing the code in its enter clause.

  * **s(1) -> s_request** is a _timed_ transition.  If we enter this state, and don't execute another transition within 1 second, we'll exit **s_request**, enter **s_request** again, re-executing the code in its enter clause.  Any other transition will cause the timed transition to be forgotten.  In the absence of an **ev_ack**, this loop will go on forever.  **s(n)** is used to indicate a timeout in terms of seconds; **ms(n)** is also available to specify timeouts in milliseconds.  Floating point values are allowed in both cases; timeouts do not need to be constant values, and will be evaluated at the time the state is entered.

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

Smax has a "load" method that reads a given file, filtering all lines not inside the "%%" sections.  There can be many of these sections in a given input file.  The canonical method for running this state machine is to ask smax to translate the machine source, then subclass the generated class with methods that actually perform the functions requested.  A Reactor instance provides the runtime support for timing and queues that the state machine uses to update itself.  To run this state machine,

    # Python code
    import os
    import smax
    r"""
    %%
    machine MyStateMachine:
        ...
    %%
    """
    MyStateMachine = smax.load(__file__, "MyStateMachine")

    class MyDevice(MyStateMachine):
        def __init__(self, reactor, serial_port_filename):
            super(MyDevice, self).__init__(reactor)
            self._fd = os.open(serial_port_filename, os.O_RDWR)
        def send(self, message):
            os.write(self._fd, message)
        def do_more_stuff(self):
            # Super important functionality goes here.
            pass

    def main():
        # Create a runtime environment that drives the state machine
        # SelectReactor uses the "select" call to block until
        # an alarm expires; you can attach your own handlers
        # to it to call events on the state machine.
        reactor = smax.SelectReactor()
        # Create the state machine instance itself
        my_device = MyDevice(reactor, "/dev/ttyS0")
        # Queue up a call to enter all the initial states
        my_device.start()
        # Run the state machine.
        reactor.run()
        # We won't get here unless someone calls reactor.stop.

A single reactor instance can handle any number of state machines.  Once you have a reactor, you can create the state machine instance; for the state machine to enter the initial state(s) you must call "start" on it.

Smax will translate the state machine specification and generate an implementation class named by the **machine** clause (MyStateMachine).  You can look at the generated code by passing an optional save_generated_python parameter to smax.load; save_generated_python will be called with the text string containing the generated python code.  Here is an excerpt from the generated code:

    class MyStateMachine(object):
        def __init__(self, reactor):
            ...
        def start(self):
            ...
        def end(self):
            ...
        def ev_ack(self):
            ...

All events are presented as methods you can call on the state machine instance.

### Reactor

A reactor provides the runtime environment for state machines.  Specifically,

- The call to reactor.run() goes into a perpetual loop, blocking until an event is observed.  When it sees an event, it calls a handler registered with that event.  You can call reactor.stop() to queue an event that will cause reactor.run() to terminate.
- All handlers executed by the reactor run in the same thread sequentially.  If that is the only thread in your program, then you don't need any locking.
- If you have other threads, you can call reactor.call(cb, *args) to schedule the reactor to call cb(*args) at the next opportunity; cb() will run in the reactor thread.  Calls are added to a queue so any number of calls can be outstanding.
- All handlers should be non blocking: the reactor won't look for the next event until the current handler returns.  If your machine stops running, it's probably because a handler is blocked on something.

Reactor is an abstract class.  smax provides some useful implementations: smax.SelectReactor, smax.AsyncioReactor, and smax.qt5.PyQtReactor.

- SelectReactor has add_fd(fd, callback) and remove_fd(fd) methods; the callback will execute when the file descriptor has data to read.
- PyQtReactor integrates with PyQt5 so that its callbacks all run in the same thread as PyQt.  The means your state machine can directly read or modify the state of a Qt UI safely.  PyQtReactor has add_fd(fd, callback) and remove_fd(fd) just like SelectReactor does.
- AsyncioReactor is described below.
- reactor.after_s(seconds, cb, *args) and reactor.after_ms(ms, cb, *args) schedule callbacks that will execute after the given amount of time has elapsed--this is how s() and ms() work.  Both methods return an object which can be used with reactor.cancel_after() to remove a callback from the alarm list.  It is always ok to cancel an alarm, even after it has executed.  after_s and after_ms are specified to accept floating point values.

Going back to our example, let's show how ev_ack should be called.  We'll use select_reactor to get a callback when serial port data is ready:

```
class MyDevice(MyStateMachine):
    ...
    def start(self):
        super(MyDevice, self).start()
        reactor.add_fd(self._fd, self.data_ready)
    def data_ready(self):
        """Called when data is available on the serial port."""
        data = os.read(self._fd, 65536)
        # A more realistic example would accumulate read data
        # until we have at least len(b"ACK") bytes available
        if data == b"ACK;":
            self.ev_ack()
```

## More complicated state machines

The above example assumes that the call to self.send() is always available-- but I happen to be working with equipment that is connected by a USB to RS232 adapter.  This creates a few new requirements:

  * The USB adapter can be disconnected--you can't send data when the device disappears.
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

  * Transitions can have conditions, indicated by an expression in brackets.  When an event is called, if the code inside the brackets evalutes to False, then the transition is ignored:

        *state s_one:
            ev_event [self.condition_a()] -> s_two
            ev_event [self.condition_b()] -> s_three
            ev_event -> s_four
        state s_two:
            pass

    For a single call to ev_event when in s_one, each condition will be evaluated in the order given in the script.  The first one that returns True will be followed and the rest will not be checked.  In this example, we'll always wind up in either s_two, s_three, or s_four, assuming that we're in s_one.  The statement "ev_event -> s_four" is considered to have a condition that is always True.  Note that a call to ev_event results in that event being queued up for execution by the reactor, so the transition (and the checking of these conditions) will happen when the reactor gets to it.

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

  * An event can transition to the inner state of another parallel state machine.  In this case, all the rest of the parallel states, including the one requesting the transition, will exit, then enter default states.  In the above example, calling **ev_y** in **s_a_2** will result in exiting **s_a_2** and **s_b_2**, and entering **s_a** and **s_b_3**.  At this time, there's no way to transition to more than one non-default state.

  * Events can be handled within a state without a transition.  In this case, the assert is never triggered because we don't actually exit the state.

        machine Example:
            *state s_a:
                ev_x: self.do_more_stuff()
            exit: assert False

  * Events can be specialized, allowing delegation to other handlers.  In this example, if you're in s_a and you call ev_specific(), you'll get a call to self.handle_special(); but if you're in s_b and you call ev_specific(), you'll get a call to self.handle_it(0).

        machine Example:
            ev_general(parameter): self.handle_it(parameter)
            *state s_a:
                ev_specific is ev_general(0) -> s_b: self.handle_special()
            state s_b:
                pass


## Macros

Frequently, the same state machine patterns occur in multiple places within your system.  For example, consider a design with multiple input switches, all of which are noisy and need debouncing.  A very reasonable approach is to have a "Debouncer" state machine, instantiated once for each switch; specific switch updates are sent to the same named method on a specific instance; that instance would know how to send out the debounced state of that input.

But consider another technique for handling this situation, which is to use a macro text substitution tool to replicate the pattern in a parent state machine.  In this case, each debouncer would run as a parallel machine within a parent state machine.  When a switch change is seen, instead of calling a common method on a specific state machine instance (as above), you'd call the switch-specific event on the parent state machine instance.  Because all active parallel machines receive all the machine's events, the debouncer now can also pay attention to global events sent to that machine (e.g. "ev_reset"); passing along debouncer results to the parent state machine becomes easy (e.g. "self.ev_switch_a_active()"); and the entire debouncer mechanism can be activated and deactivated on demand (in the same way the serial port above is deactivated when the USB controller is unplugged above).  For an example of using Jinja2 in this way, check out test/test_debounce.py.

# API

## Reactor -- the state machine runtime.

State machines keep track of the states they're in and use reactors to queue up the methods they need to execute.  If you supply your own reactor instance, the compiled state machine code will require no other external runtime support.   State machines will call these methods on a reactor:

    class Reactor:
        # Add a callback with arguments to the queue.
        def call(self, cb, *args):
            ...
        # Add a callback which will be queued after the
        # given number of seconds have elapsed.  Seconds
        # is a floating point value.  Returns
        # a handle which will be passed to cancel_after.
        def after_s(self, seconds, callback, *args):
            ...
        # Same as after_s except that the time
        # is specified in milliseconds as a floating
        # point value (ms=.1 means wait for 100 microseconds).
        def after_ms(self, ms, callback, *args):
            ...
        # Given a handle returned by after_s or
        # after_ms, cancel that timeout.  State machines
        # always cancel all their callbacks-- it
        # must be ok to cancel timers that have already
        # expired.
        def cancel_after(self, r):
            ...

Note that after_s and after_ms are specified to accept floating point values, so after_s(.001, ...) is equivalent to after_ms(1), and the reactor is specified to wait for at least the given time.  Smax provides some additional methods that your program can call:

    class Reactor: # Continued...
        # Call all the callbacks currently queued, including
        # all those whose timeouts have expired.  If there are
        # any timeouts that haven't expired yet, this method
        # returns the number of seconds (floating point) until
        # the next timeout expires; if there are no timeouts,
        # then returns None.
        def sync(self):
            ...

## Diagrams

Smax comes with a command-line tool ("smax") which loads state machine specifications and writes various outputs from that specification.  When run with "--yaml <yamlfilename>", the state machine data will be written as yaml data to the given filename; running with "--plantuml <filename>" will generate a plantuml state machine script.  Note that there is no effort made to format the plantuml state diagram, so your mileage may vary with this.

## State machine debugging

State machine behavior can be observed by overriding a handful of methods in the generated code.  state_name is an array of strings representing the name of the nested state; these are frequently represented using ".".join(state_name).

  * _state_machine_enter(self, state_name) is called when the as the state is entered.
  * _state_machine_exit(self, state_name) is called when the before the state is exited.
  * _state_machine_handle(self, state_name, event_name) is called when a state is handling the given event.
  * _state_machine_timeout(self, state_name, time_spec) is called when a state reaches a timeout; time_spec is a printable string taken from the time specification in the state machine specification.
  * _state_machine_ignored(self, event_name, *args) is called when no currently active state has a handler for the given event.
  * _state_machine_debug(self, message) -- by default, the above methods will call _state_machine_debug with a relevant value for the message parameter.

## Support for asyncio coroutines

To support programs using asyncio, smax provides an smax.AsyncioReactor which affects a state machine in two ways: the reactor.run method is awaitable, along with all state machine event methods.  AsyncioReactor.run is appropriate for use with asyncio.create_task; this can be run before or after state machines attach themselves to the reactor.  All event methods will, with this reactor, return futures that will actually execute the transition when the caller uses await.

    def main():
        event_loop = asyncio.get_event_loop()
        reactor = smax.AsyncioReactor(event_loop)
        asyncio.create_task(reactor.run())
        # It's OK to add machines to the already running reactor.
        my_state_machine = MyStateMachine(reactor)
        my_state_machine.start()
        await my_state_machine.ev_c()
        ...

In this mode, when the state machine blocks waiting for another event or timeout, control will be returned to the event loop.  Note that AsyncioReactor always serializes transitions to all its attached state machines.  It's always ok for a coroutine to call a state machine event; when run with AsyncioReactor, those calls are added to a queue that the reactor steps through sequentially.

# Gotchas

## Nested events

Each event specification results in a corresponding method in the generated state machine; calls to these event methods queue up a callback for execution by the reactor.  Events can be called from within state machine transitions, in which case the current transition will complete (and any other queued activity) before the called event is acted on.  If you call several event methods, be aware that they act on the states that are active at the time the event is executed--not the time it's queued.

## Perpetual loops and stack overflows

Mutual state machine transitions can result in an infinite loop--which usually results in a python stack overflow.  The best implementation for this type of machine is to make these transitions trigger on "s(0)".  In this case, the transition is queued up for the reactor instead of executed immediately... allowing the current transition to complete.

        machine Example:
            *state s_a:
                s(0) -> s_b
            state s_b:
                s(0) -> s_a


# License

Smax is licensed under GPLv3; please contribute back the changes you make to the translator itself.  The output generated by smax is not covered by any license (https://www.gnu.org/licenses/gpl-faq.html#WhatCaseIsOutputGPL) so you can do with that as you please.
