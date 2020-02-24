"""Routines for extracting parameter and return information from type annotations."""

import inspect
import typing
from typing import Tuple, Dict
from typedargs.basic_structures import ParameterInfo, ReturnInfo


def _get_type_name(type_class):
    type_name = getattr(type_class, '__name__', None)

    if inspect.getmodule(type_class) == typing and type_name in ('Dict', 'List', 'Tuple'):
        type_name = type_name.lower()

    return type_name


def parse_annotations(annotations: dict) -> Tuple[Dict[str, ParameterInfo], ReturnInfo]:
    """Get type info for params and return value from annotations dictionary"""

    params = {}
    returns = ReturnInfo(None, None, None, False, None)

    if 'return' in annotations:
        ret_type = annotations['return']
        type_name = _get_type_name(ret_type)
        returns = ReturnInfo(ret_type, type_name, None, True, None)

    for param_name, param_type in annotations.items():
        if param_name == 'return':
            continue

        type_name = _get_type_name(param_type)
        params[param_name] = ParameterInfo(param_type, type_name, [], None)

    return params, returns
