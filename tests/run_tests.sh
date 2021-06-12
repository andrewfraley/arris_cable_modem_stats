#!/bin/bash
# run from parent dir

FILES=tests/test_*.py
for f in $FILES
do
  echo "Running $f tests"
  filename=$(basename -- "$f")
  testfile="${filename%.*}"
  python3 -m tests.$testfile
done
