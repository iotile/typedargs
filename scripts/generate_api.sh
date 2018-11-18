#!/usr/bin/env bash

# It is very important that this script runs in python 3
# since it calls importlib.import_module which does not 
# properly work on python 2.  In particular it gets confused
# with directly importing submodules.

rm -rf doc/api

python scripts/better_apidoc.py -o doc/api ./typedargs -f -e -t doc/_template

rm doc/api/modules.rst
