"""Tests for builtin types included with typedargs."""

# This file is adapted from python code released by WellDone International
# under the terms of the LGPLv3.  WellDone International's contact information is
# info@welldone.org
# http://welldone.org
#
# Modifications to this file from the original created at WellDone International
# are copyright Arch Systems Inc.

# pylint: disable=unused-argument,redefined-outer-name,missing-docstring

import pytest
from typedargs import type_system
import typedargs
from typedargs.exceptions import ValidationError, ArgumentError


def test_builtins_exist():
    """Make sure basic builtins are found."""
    builtin = ['integer', 'path', 'string', 'basic_dict', 'bool', 'bytes', 'float']

    for type_name in builtin:
        type_system.get_type(type_name)


def test_builtin_conversions():
    """Make sure basic conversions work."""
    val = type_system.convert_to_type('42', 'integer')
    assert val == 42

    val = type_system.convert_to_type('/users/timburke', 'path')
    assert val == '/users/timburke'

    val = type_system.convert_to_type('hello', 'string')
    assert val == 'hello'


def test_annotation_correct():
    """Make sure param annotation works."""
    @typedargs.param("string_param", "string", desc='Hello')
    def function_test(string_param):  # pylint: disable=C0111,W0613
        pass

    function_test("hello")


def test_annotation_unknown_type():
    """Make sure we flag unknown types."""
    with pytest.raises(ArgumentError):
        @typedargs.param("string_param", "unknown_type", desc='Hello')
        def function_test(string_param):  # pylint: disable=C0111,W0613
            pass

        function_test("hello")


def test_annotation_validation():
    """Make sure validation works."""
    with pytest.raises(ValidationError):
        @typedargs.param("int_param", "integer", "nonnegative", desc="No desc")
        def function_test(int_param):  # pylint: disable=C0111,W0613
            pass

        function_test(-1)


def test_bool_valid():
    """Ensure bool conversion works."""
    val = type_system.convert_to_type('True', 'bool')
    assert val is True

    val = type_system.convert_to_type('false', 'bool')
    assert val is False

    val = type_system.convert_to_type(True, 'bool')
    assert val is True

    val = type_system.convert_to_type(False, 'bool')
    assert val is False

    val = type_system.convert_to_type(None, 'bool')
    assert val is None

    val = type_system.convert_to_type(0, 'bool')
    assert val is False

    val = type_system.convert_to_type(1, 'bool')
    assert val is True


def test_format_bool():
    """Ensure that bool formatting works."""
    val = type_system.format_value(True, 'bool')
    assert val == 'True'

    val = type_system.format_value(False, 'bool')
    assert val == 'False'


def test_unicode_conversion():
    """Make sure that converting to builtin types from unicode works."""

    # Test bool
    val = type_system.convert_to_type(u'True', 'bool')
    assert val is True

    val = type_system.convert_to_type(u'False', 'bool')
    assert val is False

    # Test int
    val = type_system.convert_to_type(u'42', 'integer')
    assert val == 42

    # Test float
    val = type_system.convert_to_type(u'42.5', 'float')
    assert val == 42.5


def test_bytes_from_hex():
    """Make sure we can convert a hex string to bytes."""

    val = type_system.convert_to_type(u'0xabcd', 'bytes')
    val2 = type_system.convert_to_type('0xabcd', 'bytes')

    assert val == val2
    assert val == bytearray(b'\xab\xcd')
