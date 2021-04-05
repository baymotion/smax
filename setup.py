#

from setuptools import setup
import sys

# Yapps doesn't seem to install
# properly without this.
sys.dont_write_bytecode = True

setup(
    name="smax",
    version="1.0",
    packages=["smax"],
    install_requires=[
        "yapps",
        "jinja2",
        "pyyaml",
    ],
    )

