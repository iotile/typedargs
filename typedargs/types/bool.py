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
from typing import Optional
from .base import BaseType


class BoolType(BaseType):
    MAPPED_BUILTIN_TYPE = bool
    MAPPED_TYPE_NAMES = ('bool', )

    @classmethod
    def FromString(cls, arg: str) -> Optional[bool]:
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

    @classmethod
    def default_formatter(cls, arg: bool) -> str:
        return str(arg)
