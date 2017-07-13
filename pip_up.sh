#!/usr/bin/env bash

echo "Uploading to pip"
set -x
test -e "tests/test_mdvl.py" || exit 1

rm -rf dist
pandoc README.md -o README.rst
python setup.py clean sdist bdist_wheel
twine upload dist/*




