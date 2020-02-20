"""Routines for extracting parameter and return information from type annotations."""

from typing import Tuple, Dict
from typedargs.basic_structures import ParameterInfo, ReturnInfo


def parse_annotations(annotations: dict) -> Tuple[Dict[str, ParameterInfo], ReturnInfo]:
    """Get type info for params and return value from annotations dictionary"""

    params = {}
    returns = ReturnInfo(None, None, None, False, None)

    if 'return' in annotations:
        ret_type = annotations.pop('return')
        returns = ReturnInfo(ret_type, None, None, True, None)

    for param_name, param_type in annotations.items():
        params[param_name] = ParameterInfo(param_type, None, [], None)

    return params, returns
