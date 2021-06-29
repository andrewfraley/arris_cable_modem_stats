#!/bin/bash
# run from parent dir
export PYTHONPATH=./src
python3 -m unittest discover -v -s tests/ -p test_*.py

# pylint src/
# pycodestyle src/
