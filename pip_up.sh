#!/usr/bin/env bash

echo "Uploading to pip"
set -x
test -e "./tests/test_mdvl.py" || exit 1

clean () {
    rm -rf ./dist
    rm -rf ./mdvl.egg-info
    rm -rf ./__pycache__
    rm -rf ./build
}
clean
pandoc ./README.md -o README.rst
python setup.py clean sdist bdist_wheel
twine upload ./dist/*
clean







