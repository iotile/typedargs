# This file is adapted from python code released by WellDone International
# under the terms of the LGPLv3.  WellDone International's contact information is
# info@welldone.org
# http://welldone.org
#
# Modifications to this file from the original created at WellDone International
# are copyright Arch Systems Inc.

# pylint: disable=unused-argument,missing-docstring

import os.path
from .base import BaseType
from typing import Optional


class PathType(BaseType):

    MAPPED_TYPE_NAMES = ('path', )

    @classmethod
    def FromString(cls, arg: str) -> Optional[str]:
        if arg is None:
            return None

        return str(arg)

    @classmethod
    def validate_readable(cls, arg: str):
        if arg is None:
            raise ValueError("Path must be readable")

        if not os.path.isfile(arg):
            raise ValueError("Path is not a file")

        try:
            file = open(arg, "r")
            file.close()
        except:
            raise ValueError("Path could not be opened for reading")

    @classmethod
    def validate_exists(cls, arg: str):
        if arg is None:
            raise ValueError("Path must exist")

        if not os.path.exists(arg):
            raise ValueError("Path must exist")

    @classmethod
    def validate_writeable(cls, arg: str):
        if arg is None:
            raise ValueError("Path must be writable")

        parent = os.path.dirname(arg)
        if not os.path.isdir(parent):
            raise ValueError("Parent directory does not exist and path must be writeable")

    @classmethod
    def default_formatter(cls, arg: str) -> str:
        return str(arg)
