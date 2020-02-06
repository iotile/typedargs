"""Routines for extracting parameter and return information from an annotation."""
from .basic_structures import ParameterInfo, ReturnInfo
from .typeinfo import TypeSystem


def parse_annotations(annotations: dict):
    """Get type info for params and return value from annotations dictionary"""

    params = {}
    returns = ReturnInfo(None, None, None, None, None)

    if 'return' in annotations:
        ret_type = annotations.pop('return')
        ret_type_name = TypeSystem.get_type_name(ret_type)
        returns = ReturnInfo(ret_type, ret_type_name, None, True, None)

    for param_name, param_type in annotations.items():
        param_type_name = TypeSystem.get_type_name(param_type)
        params.update({param_name: ParameterInfo(param_type, param_type_name, [], None)})

    return params, returns
