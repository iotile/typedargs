# This file is adapted from python code released by WellDone International
# under the terms of the LGPLv3.  WellDone International's contact information is
# info@welldone.org
# http://welldone.org
#
# Modifications to this file from the original created at WellDone International
# are copyright Arch Systems Inc.

# pylint: disable=unused-argument,missing-docstring
from typing import Optional, Iterable
from .base import BaseType


class StringType(BaseType):
    MAPPED_BUILTIN_TYPE = str

    @classmethod
    def FromString(cls, arg: str) -> Optional[str]:
        if arg is None:
            return None

        return str(arg)

    @classmethod
    def default_formatter(cls, arg: str) -> str:
        return arg

    @classmethod
    def validate_list(cls, arg: str, choices: Iterable):
        """
        Make sure the argument is in the list of choices passed to the function
        """

        if arg not in choices:
            raise ValueError('Value not in list: %s' % str(choices))

    @classmethod
    def validate_not_empty(cls, arg: str):
        """
        Make sure the string is not empty
        """

        if len(arg) == 0:
            raise ValueError("String cannot be empty")

    @classmethod
    def format_repr(cls, arg: str) -> str:
        return repr(arg)
