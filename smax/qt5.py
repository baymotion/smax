# This file is part of the smax project (http://github.com/baymotion/smax)
# and is copyrighted under GPL v3 or later.

# Reactor that works with PyQt5 so that the entire application
# works in a single thread.

try:
    from PyQt5 import QtCore, QtGui, QtWidgets
except ModuleNotFoundError:
    from PySide2 import QtCore, QtGui, QtWidgets

import smax
import smax.log as log


class PyQtReactor(smax.Reactor):
    class Adapter(QtCore.QObject):
        _queue_update = QtCore.pyqtSignal(object)

        def __init__(self, reactor):
            super(PyQtReactor.Adapter, self).__init__()
            self._reactor = reactor
            self._o = []  # objects we want to keep references to
            self._queue_update.connect(self.execute)
            self._timer = QtCore.QTimer()
            self._timer.timeout.connect(self.timeout)
            self._timer.setSingleShot(True)

        def execute(self, cb):
            self._timer.stop()
            cb()

        def signal(self, cb):
            self._queue_update.emit(cb)

        def schedule(self, timeout, cb):
            self._timer.stop()
            self.timeout_cb = cb
            self._timer.start(timeout * 1000.0)

        def timeout(self):
            self.timeout_cb()

        def add_fd(self, fd, read_callback):
            notifier = QtCore.QSocketNotifier(fd, QtCore.QSocketNotifier.Read)
            notifier.activated.connect(read_callback)
            self._o.append(notifier)

        def remove_fd(self, fd):
            for n, o in enumerate(
                self._o[:]
            ):  # iterate over a copy so we can delete the element
                if o.socket() == fd:
                    self._o.pop(n)
                    return

    def __init__(self):
        super(PyQtReactor, self).__init__()
        self._adapter = PyQtReactor.Adapter(self)

    def _signal(self):
        self._adapter.signal(self._run)

    def _run(self):
        timeout = self.sync()
        if self.done():
            return
        # timeout may be None
        log.trace("timeout=%s." % timeout)
        if timeout is not None:
            self._adapter.schedule(timeout, self._run)

    def add_fd(self, fd, read_callback):
        self._adapter.add_fd(fd, read_callback)

    def remove_fd(self, fd):
        self._adapter.remove_fd(fd)


def machine(spec, machine_name):
    for m in spec["spec"]:
        if "machine" not in m:
            continue
        machine = m["machine"]
        if machine.name != machine_name:
            continue
        return machine
    return None


NEST = "NEST"
UNNEST = "UNNEST"


def states(state):
    yield state
    if not state.inner_states:
        return
    yield NEST
    for sl in state.inner_states:
        for s in sl:
            for ss in states(s):
                yield ss
    yield UNNEST


def state_tree(machine, tree_widget):
    r = {}
    parent = [tree_widget]
    last = None
    items = []
    for s in states(machine):
        if s == NEST:
            parent.insert(0, last)
            continue
        if s == UNNEST:
            parent.pop(0)
            continue
        item = QtWidgets.QTreeWidgetItem(parent[0], [s.name])
        r[s.dot_name] = item
        last = item
        items.append(item)
    tree_widget.addTopLevelItems(items)
    for item in items:
        item.setExpanded(True)
        item.setCheckState(0, QtCore.Qt.Unchecked)
        item.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)
    return r


class EventWidget(QtWidgets.QWidget):
    def __init__(self, instance, event, parent=None):
        super(EventWidget, self).__init__(parent)
        self._event = event
        self._layout = QtGui.QHBoxLayout(self)
        self._control = QtGui.QPushButton(event.name, self)
        self._layout.addWidget(self._control)
        parameters = {}
        for arg in event.args:
            text_edit = QtGui.QLineEdit(self)
            self._layout.addWidget(QtGui.QLabel(arg))
            self._layout.addWidget(text_edit)
            parameters[arg] = text_edit
        method = getattr(instance, event.name)

        def go(state, method=method, event=event, parameters=parameters):
            args = [str(parameters[arg].text()) for arg in event.args]
            method(*args)

        self._control.clicked.connect(go)
        self.setLayout(self._layout)


def event_controls(machine, instance, scroll_area):
    events = {e.name: e for e in machine.events}
    keys = sorted(events.keys())
    for k in keys:
        ew = EventWidget(instance, events[k], scroll_area)
        list_item = QtGui.QListWidgetItem(scroll_area)
        list_item.setSizeHint(ew.sizeHint())
        scroll_area.addItem(list_item)
        scroll_area.setItemWidget(list_item, ew)
