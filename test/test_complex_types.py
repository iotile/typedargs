"""Tests to ensure that recursive complex types work."""

# This file is adapted from python code released by WellDone International
# under the terms of the LGPLv3.  WellDone International's contact information is
# info@welldone.org
# http://welldone.org
#
# Modifications to this file from the original created at WellDone International
# are copyright Arch Systems Inc.

# pylint: disable=unused-argument,redefined-outer-name

import pytest
from typedargs import type_system
from typedargs.exceptions import ValidationError


def test_splitting():
    """Make sure we properly split complex types."""
    base, is_complex, subs = type_system.split_type('map(string, integer)')
    assert base == 'map'
    assert is_complex is True
    assert len(subs) == 2
    assert subs[0] == 'string'
    assert subs[1] == 'integer'


def test_map_type():
    """Make sure the map type works."""
    type_system.get_type('map(string, string)')


def test_map_formatting():
    """Make sure we can format map types."""
    val = {'hello': 5}

    formatted = type_system.format_value(val, 'map(string, integer)')
    assert formatted == 'hello: 5'


def test_list_type():
    """Make sure the list type works."""
    type_system.get_type('list(integer)')


def test_list_formatting():
    """Make sure we can format lists."""
    val = [10, 15]

    formatted = type_system.format_value(val, 'list(integer)')
    assert formatted == "10\n15"


def test_list_conversion():
    """Make sure we can convert strings to lists."""

    out = type_system.convert_to_type("[1, 2, 3]", 'list(integer)')
    assert out == [1, 2, 3]

    out = type_system.convert_to_type("['abc', 'def', 'g']", 'list(string)')
    assert out == ['abc', 'def', 'g']

    with pytest.raises(ValidationError):
        out = type_system.convert_to_type("['abc', 'def', 'g']", 'list(integer)')

    with pytest.raises(ValidationError):
        out = type_system.convert_to_type("abc", 'list(str)')

    with pytest.raises(ValidationError):
        out = type_system.convert_to_type("{'abc': 'def'}", 'list(string)')

    out = type_system.convert_to_type([1, 2, 3], 'list(integer)')
    assert out == [1, 2, 3]

    out = type_system.convert_to_type(None, 'list(integer)')
    assert out is None
