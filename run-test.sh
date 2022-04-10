#

set -o errexit
set -o xtrace

python3 -m venv _python
_python/bin/pip install -r requirements.txt
_python/bin/python3 setup.py develop
_python/bin/pytest -s test
