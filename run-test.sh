#

set -o errexit
set -o xtrace

python3 -m venv _python
#source venv/bin/activate
_python/bin/pip install pytest
_python/bin/pip install pyqt5
_python/bin/pip install PySide2
_python/bin/pip install pudb
_python/bin/pip install pytest-pudb
#python3 setup.py install
_python/bin/python3 setup.py develop

_python/bin/pytest -s test
#_python/bin/pytest --pudb -s test/test_conditions.py
#_python/bin/pytest -s test/test_conditions.py
#_python/bin/pytest -s test/test_basic.py
#_python/bin/pytest -s test/test_debounce.py
