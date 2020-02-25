# This file is adapted from python code released by WellDone International
# under the terms of the LGPLv3.  WellDone International's contact information is
# info@welldone.org
# http://welldone.org
#
# Modifications to this file from the original created at WellDone International
# are copyright Arch Systems Inc.

# pylint: disable=unused-argument,missing-docstring

# integer type
from typing import Optional
from .base import BaseType


class IntegerType(BaseType):
    MAPPED_BUILTIN_TYPE = int
    MAPPED_TYPE_NAMES = ('integer', 'int')

    @classmethod
    def FromString(cls, arg: str) -> Optional[int]:
        if arg is None:
            return None

        if isinstance(arg, str):
            return int(arg, 0)
        if isinstance(arg, int):
            return arg

        raise TypeError("Unknown argument type")

    @classmethod
    def validate_positive(cls, arg: int):
        if arg is None:
            return

        if arg <= 0:
            raise ValueError("value is not positive")

    @classmethod
    def validate_range(cls, arg: int, lower: int, upper: int):
        if arg is None:
            return

        if arg < lower or arg > upper:
            raise ValueError("not in required range [%d, %d]" % (int(lower), int(upper)))

    @classmethod
    def validate_nonnegative(cls, arg: int):
        if arg is None:
            return

        if arg < 0:
            raise ValueError("value is negative")

    @classmethod
    def default_formatter(cls, arg: int) -> str:
        return str(arg)

    @classmethod
    def format_unsigned(cls, arg: int) -> str:
        return format(arg, 'd')

    @classmethod
    def format_hex(cls, arg: int) -> str:
        return "0x%X" % arg
