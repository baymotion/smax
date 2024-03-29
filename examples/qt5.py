# qt.py tests the PyQtReactor.
#
# The state machine's reactor is driven
# by the pyqt event loop so we can do whatever UI
# updates we want without reentrancy problems.
# This is demonstrated by enabling various
# checkboxes on the display, and the program
# exits after the last box is checked.
# Because the checkboxes are all disabled
# when the screen is initialized, the only
# way you can properly exit this program is
# to click each box as it becomes enabled.
#
# This test also demonstrates hooking into
# signals generated by the UI to become
# events in the state machine.
#
# Finally, if your UI has a QTreeWidget somwhere
# in it, you can pass that to smax.state_tree().
# state_tree(), given that tree widget and the
# spec for a state machine, will populate the
# widget with a set of QTreeItems, where each
# item corresponds with a state from your state
# machine.  state_tree returns a dict of these
# QTreeItems, which are handy when used with
# _state_machine_enter and _state_machine_exit.
# In those methods, look up the given state
# in the dict, and call setCheckState to
# update your UI with a complete view of
# the state of your system.
#

import os
from PyQt5 import QtCore, uic
from PyQt5.QtWidgets import QApplication
import smax
import smax.qt5
import sys

r"""
%%
machine QtTestStateMachine:
    *state s_a:
        enter: self._view.checkbox_a.setEnabled(True)
        exit: self._view.checkbox_a.setEnabled(False)
        ev_checkbox_a(state) -> s_b
    state s_b:
        enter: self._view.checkbox_b.setEnabled(True)
        exit: self._view.checkbox_b.setEnabled(False)
        ev_checkbox_b(state) -> s_c
    state s_c:
        enter: self._view.checkbox_c.setEnabled(True)
        exit: self._view.checkbox_c.setEnabled(False)
        ev_checkbox_c(state): self.done()
%%
"""


def save_generated_python(s):
    with open(".generated_state_machine.py", "wt") as f:
        f.write(s)


QtTestStateMachine = smax.load(
    __file__, "QtTestStateMachine", save_generated_python=save_generated_python
)
state_machine_spec = smax.spec(__file__)
state_machine = smax.qt5.machine(state_machine_spec, "QtTestStateMachine")


class QtTest(QtTestStateMachine):
    def __init__(self, reactor, view, controller, state_tree):
        super(QtTest, self).__init__(reactor)
        self._view = view
        self._controller = controller
        self._state_tree = state_tree
        view.checkbox_a.clicked.connect(
            lambda state: self.ev_checkbox_a(state),
        )
        view.checkbox_b.clicked.connect(
            lambda state: self.ev_checkbox_b(state),
        )
        view.checkbox_c.clicked.connect(
            lambda state: self.ev_checkbox_c(state),
        )

    def done(self):
        self._controller.close()

    def _state_machine_enter(self, state_name):
        s = ".".join(state_name)
        self._state_tree[s].setCheckState(0, QtCore.Qt.Checked)

    def _state_machine_exit(self, state_name):
        s = ".".join(state_name)
        self._state_tree[s].setCheckState(0, QtCore.Qt.Unchecked)


def main():
    app = QApplication(sys.argv)
    View, Controller = uic.loadUiType(
        os.path.join(os.path.dirname(__file__), "qt5.ui"),
    )
    controller = Controller(parent=None)
    view = View()
    view.setupUi(controller)
    reactor = smax.qt5.PyQtReactor()
    state_tree = smax.qt5.state_tree(state_machine, view.states)
    test = QtTest(reactor, view, controller, state_tree)
    test.start()
    controller.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
