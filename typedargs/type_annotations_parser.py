"""Routines for extracting parameter and return information from an annotation."""
from .basic_structures import ParameterInfo, ReturnInfo


def parse_annotations(annotations: dict):
    """Get type info for params and return value from annotations dictionary"""

    params = {}
    returns = ReturnInfo(None, None, None, None)

    if 'return' in annotations:
        ret_type = annotations.pop('return')
        returns = ReturnInfo(ret_type, None, True, None)

    for param_name, param_type in annotations.items():
        params.update({param_name: ParameterInfo(param_type, [], None)})

    return params, returns
