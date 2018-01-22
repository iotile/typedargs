"""A strong typing system with command line REPL environment for Python 2 and 3 code."""

# This file is adapted from python code released by WellDone International
# under the terms of the LGPLv3.  WellDone International's contact information is
# info@welldone.org
# http://welldone.org
#
# Modifications to this file from the original created at WellDone International
# are copyright Arch Systems Inc.

# External API functions from this package

from typedargs.annotate import (docannotate, param, returns, context, finalizer,
                                takes_cmdline, annotated, return_type, stringable)
from typedargs.typeinfo import type_system, iprint
