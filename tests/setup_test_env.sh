#!/bin/bash

set -e
python -m pip install --upgrade pip
python3 -m venv venv
. venv/bin/activate
python3 -m pip install -r src/requirements.txt
