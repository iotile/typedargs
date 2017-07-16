"""Test the annotation of return type information."""

# This file is adapted from python code released by WellDone International
# under the terms of the LGPLv3.  WellDone International's contact information is
# info@welldone.org
# http://welldone.org
#
# Modifications to this file from the original created at WellDone International
# are copyright Arch Systems Inc.

import typedargs
from typedargs import type_system

def test_simplereturntype():
    """Make sure we can annotate a simple return type."""

    @typedargs.return_type("string")
    def returns_string():  # pylint: disable=C0111,W0613
        return "hello"

    val = returns_string()
    formed = type_system.format_return_value(returns_string, val)

    assert formed == "hello"


def test_complexreturntype():
    """Make sure we can annotate a complex return type."""

    @typedargs.return_type("map(string, integer)")
    def returns_map():  # pylint: disable=C0111,W0613
        return {"hello": 5}

    val = returns_map()
    formed = type_system.format_return_value(returns_map, val)

    assert formed == "hello: 5"
