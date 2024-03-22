#!/usr/bin/env sh

set -e -x

./node_modules/.bin/prettier --write utilities/console-injector.js static/ templates/
yapf -i *.py utilities/*.py
