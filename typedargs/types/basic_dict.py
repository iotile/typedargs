# pylint: disable=unused-argument,missing-docstring

import json
from typedargs.exceptions import ValidationError


MAPPED_BUILTIN_TYPE = dict
MAPPED_TYPE_NAMES = ('dict', )


def convert(arg, **kwargs):
    if arg is None:
        return None

    if isinstance(arg, str):
        return json.loads(arg)
    if isinstance(arg, dict):
        return arg

    raise TypeError("Unknown argument type")


def _json_formatter(arg):
    if isinstance(arg, bytearray):
        return repr(arg)

    return str(arg)


def default_formatter(arg, **kwargs):
    return json.dumps(arg, sort_keys=True, indent=4, separators=(',', ': '), default=_json_formatter)
