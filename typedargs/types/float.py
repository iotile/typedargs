# This file is adapted from python code released by WellDone International
# under the terms of the LGPLv3.  WellDone International's contact information is
# info@welldone.org
# http://welldone.org
#
# Modifications to this file from the original created at WellDone International
# are copyright Arch Systems Inc.

# pylint: disable=unused-argument,missing-docstring
from typing import Optional, Union
from .base import BaseInternalType


class InternalFloat(BaseInternalType):
    MAPPED_BUILTIN_TYPE = float
    MAPPED_TYPE_NAMES = ('float', )

    @classmethod
    def FromString(cls, arg: str) -> Optional[float]:
        if arg is None:
            return None

        if isinstance(arg, (str, int, float)):
            return float(arg)

        raise TypeError("Unknown argument type")

    @classmethod
    def validate_positive(cls, arg: float):
        if arg is None:
            return

        if arg <= 0:
            raise ValueError("value is not positive")

    @classmethod
    def validate_nonnegative(cls, arg: float):
        if arg is None:
            return

        if arg < 0:
            raise ValueError("value is negative")

    @classmethod
    def validate_range(cls, arg: float, lower: Union[int, float], upper: Union[int, float]):
        if arg is None:
            return

        if arg < lower or arg > upper:
            raise ValueError("not in required range [%f, %f]" % (float(lower), float(upper)))

    @classmethod
    def default_formatter(cls, arg: float) -> str:
        return str(arg)
