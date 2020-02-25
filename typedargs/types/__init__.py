"""Builtin types that come prestocked in typedargs."""

# This file is adapted from python code released by WellDone International
# under the terms of the LGPLv3.  WellDone International's contact information is
# info@welldone.org
# http://welldone.org
#
# Modifications to this file from the original created at WellDone International
# are copyright Arch Systems Inc.

#Known Types
from .bool import InternalBool
from .string import InternalString
from .basic_dict import InternalDict
from .float import InternalFloat
from .bytes import InternalBytes
from .path import InternalPath
from .integer import InternalInteger

from .map import map
from .list import list
