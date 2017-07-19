"""Test the annotation of return type information."""

# This file is adapted from python code released by WellDone International
# under the terms of the LGPLv3.  WellDone International's contact information is
# info@welldone.org
# http://welldone.org
#
# Modifications to this file from the original created at WellDone International
# are copyright Arch Systems Inc.

# pylint: disable=unused-argument,redefined-outer-name

import typedargs


def test_simplereturntype():
    """Make sure we can annotate a simple return type."""

    @typedargs.return_type("string")
    def returns_string():  # pylint: disable=C0111,W0613
        return "hello"

    val = returns_string()
    formed = returns_string.metadata.format_returnvalue(val)
    assert formed == "hello"


def test_complexreturntype():
    """Make sure we can annotate a complex return type."""

    @typedargs.return_type("map(string, integer)")
    def returns_map():  # pylint: disable=C0111,W0613
        return {"hello": 5}

    val = returns_map()
    formed = returns_map.metadata.format_returnvalue(val)
    assert formed == "hello: 5"


def test_stringable_returnvalue():
    """Make sure stringable works."""

    @typedargs.stringable
    def returns_stringable(): # pylint: disable=C0111,W0613
        return True

    val = returns_stringable()
    formed = returns_stringable.metadata.format_returnvalue(val)
    assert formed == "True"
