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
    builtin = ['integer', 'int', 'path', 'string', 'str', 'basic_dict', 'dict', 'bool', 'bytes', 'float']

    for type_name in builtin:
        type_system.get_proxy_for_type(type_name)


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


def test_format_bool():
    """Ensure that bool formatting works."""
    val = type_system.format_value(True, 'bool')
    assert val == 'True'

    val = type_system.format_value(False, 'bool')
    assert val == 'False'


def test_bytes_from_hex():
    """Make sure we can convert a hex string to bytes."""

    val = type_system.convert_to_type(u'0xabcd', 'bytes')
    val2 = type_system.convert_to_type('0xabcd', 'bytes')

    assert val == val2
    assert val == bytearray(b'\xab\xcd')


def test_bytes_hex_formatting():
    """Make sure we can convert a bytes object to hex."""

    assert type_system.format_value(b'\xab\xcd', 'bytes', 'hex') == 'abcd'
    assert type_system.format_value(bytearray([0xab, 0xcd]), 'bytes', 'hex') == 'abcd'
    assert type_system.format_value(b'', 'bytes', 'hex') == ''


EXPECTED_HEXDUMP = \
"""00000000  00 01 02 03 04 05 06 07 08 09 0a 0b 0c 0d 0e 0f  ................
00000010  10 11 12 13 14 15 16 17 18 19 1a 1b 1c 1d 1e 1f  ................
00000020  20 21 22 23 24 25 26 27 28 29 2a 2b 2c 2d 2e 2f   !"#$%&'()*+,-./
00000030  30 31 32 33 34 35 36 37 38 39 3a 3b 3c 3d 3e 3f  0123456789:;<=>?
00000040  40 41 42 43 44 45 46 47 48 49 4a 4b 4c 4d 4e 4f  @ABCDEFGHIJKLMNO
00000050  50 51 52 53 54 55 56 57 58 59 5a 5b 5c 5d 5e 5f  PQRSTUVWXYZ[\\]^_
00000060  60 61 62 63 64 65 66 67 68 69 6a 6b 6c 6d 6e 6f  `abcdefghijklmno
00000070  70 71 72 73 74 75 76 77 78 79 7a 7b 7c 7d 7e 7f  pqrstuvwxyz{|}~.
00000080  80 81 82 83 84 85 86 87 88 89 8a 8b 8c 8d 8e 8f  ................
00000090  90 91 92 93 94 95 96 97 98 99 9a 9b 9c 9d 9e 9f  ................
000000a0  a0 a1 a2 a3 a4 a5 a6 a7 a8 a9 aa ab ac ad ae af  ................
000000b0  b0 b1 b2 b3 b4 b5 b6 b7 b8 b9 ba bb bc bd be bf  ................
000000c0  c0 c1 c2 c3 c4 c5 c6 c7 c8 c9 ca cb cc cd ce cf  ................
000000d0  d0 d1 d2 d3 d4 d5 d6 d7 d8 d9 da db dc dd de df  ................
000000e0  e0 e1 e2 e3 e4 e5                                ......"""


def test_bytes_hexdump_formatting():
    """Make sure we can convert a bytes object to a hexdump."""

    data = bytes(range(0, 230))

    val = type_system.format_value(data, 'bytes', 'hexdump')
    print(val)

    assert val == EXPECTED_HEXDUMP
