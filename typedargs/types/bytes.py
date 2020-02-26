# This file is copyright Arch Systems, Inc.
# Except as otherwise provided in the relevant LICENSE file, all rights are reserved.

# pylint: disable=unused-argument,missing-docstring

#bytes.py
#Simple bytearray type

import sys
from binascii import unhexlify, hexlify

MAPPED_BUILTIN_TYPE = bytes

def convert(arg, **kwargs):
    if isinstance(arg, bytearray):
        return arg
    if isinstance(arg, str):
        if len(arg) > 2 and arg.startswith("0x"):
            data = unhexlify(arg[2:])
        else:
            data = arg

        return bytearray(data)
    if isinstance(arg, bytes):
        return arg

    raise TypeError("You must create a bytes object from bytes, bytearray or a hex string")


def convert_binary(arg, **kwargs):
    return bytearray(arg)


def default_formatter(arg, **kwargs):
    return str(arg)


def format_repr(arg):
    return repr(arg)


def format_hex(arg):
    """Convert the bytes object to a hex string."""

    return hexlify(arg).decode('utf-8')


def format_hexdump(arg):
    """Convert the bytes object to a hexdump.

    The output format will be:

    <offset, 4-byte>  <16-bytes of output separated by 1 space>  <16 ascii characters>
    """

    line = ''

    for i in range(0, len(arg), 16):
        if i > 0:
            line += '\n'
        chunk = arg[i:i + 16]
        hex_chunk = hexlify(chunk).decode('utf-8')
        hex_line = ' '.join(hex_chunk[j:j + 2] for j in range(0, len(hex_chunk), 2))

        if len(hex_line) < (3 * 16) - 1:
            hex_line += ' ' * (((3 * 16) - 1) - len(hex_line))

        ascii_line = ''.join(_convert_to_ascii(x) for x in chunk)
        offset_line = '%08x' % i

        line += "%s  %s  %s" % (offset_line, hex_line, ascii_line)

    return line


def _convert_to_ascii(byte):
    if byte < 32 or byte > 126:
        return '.'

    return chr(byte)
