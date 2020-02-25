# This file is adapted from python code released by WellDone International
# under the terms of the LGPLv3.  WellDone International's contact information is
# info@welldone.org
# http://welldone.org
#
# Modifications to this file from the original created at WellDone International
# are copyright Arch Systems Inc.

# pylint: disable=unused-argument,missing-docstring

# bool.py
# Simple boolean type

MAPPED_BUILTIN_TYPE = bool

def convert(arg, **kwargs):
    if arg is None:
        return arg

    if isinstance(arg, str):
        comp = str(arg.lower())

        if comp == u'true':
            return True
        if comp == u'false':
            return False

        raise ValueError("Unknown boolean value (should be true or false): %s" % arg)

    return bool(arg)


def default_formatter(arg, **kwargs):
    return str(arg)
