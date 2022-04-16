#

set -o errexit
set -o xtrace

_python/bin/smax --yaml test.yaml test/test_substates.py
