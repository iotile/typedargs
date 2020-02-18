"""Routines for extracting parameter and return information from type annotations."""

from typing import Tuple, Dict
from typedargs.typeinfo import TypeSystem
from typedargs.basic_structures import ParameterInfo, ReturnInfo


def parse_annotations(annotations: dict) -> Tuple[Dict[str, ParameterInfo], ReturnInfo]:
    """Get type info for params and return value from annotations dictionary"""

    params = {}
    returns = ReturnInfo(None, None, None, False, None)

    # todo: Remove ret_type_name after switching to type classes instead of type modules
    # todo: But make sure that type mismatch warning is logged in occasion
    if 'return' in annotations:
        ret_type = annotations.pop('return')
        ret_type_name = TypeSystem.get_type_name(ret_type)
        returns = ReturnInfo(ret_type, ret_type_name, None, True, None)

    for param_name, param_type in annotations.items():
        param_type_name = TypeSystem.get_type_name(param_type)
        params[param_name] = ParameterInfo(param_type, param_type_name, [], None)

    return params, returns
