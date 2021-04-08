#

set -o errexit
set -o xtrace

python3 -m venv venv
source venv/bin/activate
pip install pytest
pip install pyqt5
pip install PySide2
#python3 setup.py install
python3 setup.py develop
pytest -s test
