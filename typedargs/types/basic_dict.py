# pylint: disable=unused-argument,missing-docstring

import json
from typing import Optional, Union
from .base import BaseType


class DictType(BaseType):
    MAPPED_BUILTIN_TYPE = dict
    MAPPED_TYPE_NAMES = ('dict', )

    @classmethod
    def FromString(cls, arg: str) -> Optional[dict]:
        if arg is None:
            return None

        if isinstance(arg, str):
            return json.loads(arg)
        if isinstance(arg, dict):
            return arg

        raise TypeError("Unknown argument type")

    @classmethod
    def _json_formatter(cls, arg: Union[dict, bytearray]):
        if isinstance(arg, bytearray):
            return repr(arg)

        return str(arg)

    @classmethod
    def default_formatter(cls, arg: Union[dict, bytearray],):
        return json.dumps(arg, sort_keys=True, indent=4, separators=(',', ': '), default=cls._json_formatter)
