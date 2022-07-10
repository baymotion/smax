#

import os
from setuptools import setup
import sys

# Yapps doesn't seem to install
# properly without this.
sys.dont_write_bytecode = True

here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, "README.md"), "rt") as f:
    long_description = f.read()
long_description_content_type = "text/markdown"

# Load the package's __version__.py module as a dictionary.
about = {}
with open(os.path.join(here, "smax", "__version__.py")) as f:
    exec(f.read(), about)

setup(
    name="smax_dsl",
    description="smax: a DSL for Harel state machines in Python.",
    author="Patrick O'Grady",
    author_email="patrick.ogrady.gm@gmail.com",
    url="https://github.com/baymotion/smax",
    version=about["__version__"],
    packages=["smax"],
    install_requires=[
        "yapps",
        "jinja2",
        "pyyaml",
    ],
    entry_points={
        "console_scripts": [
            "smax=smax.__main__:main",
        ],
    },
    long_description=long_description,
    long_description_content_type=long_description_content_type,
    test_suite="tests",
    license="GPLv3",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
    ],
)
