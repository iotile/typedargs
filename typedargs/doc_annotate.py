"""Routines for extracting parmeter and return information from a docstring."""

from __future__ import (unicode_literals, print_function, absolute_import)
from builtins import str
import inspect
from .exceptions import ValidationError
from .basic_structures import ParameterInfo, ReturnInfo


def parse_docstring(doc):
    """Parse a docstring into ParameterInfo and ReturnInfo objects."""

    doc = inspect.cleandoc(doc)
    lines = doc.split('\n')
    section = None
    section_indent = None

    params = {}
    returns = None

    for line in lines:
        line = line.rstrip()

        if len(line) == 0:
            continue
        elif str(line) == 'Args:':
            section = 'args'
            section_indent = None
            continue
        elif str(line) == 'Returns:':
            section = 'return'
            section_indent = None
            continue

        if section is not None:
            stripped = line.lstrip()
            margin = len(line) - len(stripped)

            if section_indent is None:
                section_indent = margin

            if margin != section_indent:
                continue

            # These are all the param lines in the docstring that are
            # not continuations of the previous line
            if section == 'args':
                param_name, type_info = parse_param(stripped)
                params[param_name] = type_info
            elif section == 'return':
                returns = parse_return(stripped)

    return params, returns


def parse_param(param):
    """Parse a single typed parameter statement."""

    param_def, _colon, _desc = param.partition(':')
    if _colon == "":
        raise ValidationError("Invalid parameter declaration in docstring, missing colon", declaration=param)

    param_name, _space, param_type = param_def.partition(' ')
    if len(param_type) < 2 or param_type[0] != '(' or param_type[-1] != ')':
        raise ValidationError("Invalid parameter type string not enclosed in ( ) characters", param_string=param_def, type_string=param_type)

    param_type = param_type[1:-1]
    return param_name, ParameterInfo(param_type, [], None)


def parse_return(return_line):
    """Parse a single return statement declaration."""

    ret_def, _colon, _desc = return_line.partition(':')
    if _colon == "":
        raise ValidationError("Invalid return declaration in docstring, missing colon", declaration=ret_def)

    return ReturnInfo(ret_def, None, True, None)
