"""Routines for extracting parameter and return information from a docstring."""

import inspect
from .doc_parser import parse_param, parse_return


def parse_docstring(doc, validate_type=True):
    """Parse a docstring into ParameterInfo and ReturnInfo objects.

    Args:
        doc (str): docstring to parse
        validate_type (bool): True if ValidationError should be raised
            where type is not specified for arg or return value.

    Returns:
        Tuple[Dict[str, ParameterInfo], Union[ReturnInfo, None]]: type information from passed docstring
    """

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

            if margin == 0:
                section = None
                section_indent = None
                continue

            if section_indent is None:
                section_indent = margin

            if margin != section_indent:
                continue

            # These are all the param lines in the docstring that are
            # not continuations of the previous line
            if section == 'args':
                param_name, type_info = parse_param(stripped, validate_type=validate_type)
                params[param_name] = type_info
            elif section == 'return':
                returns = parse_return(stripped, validate_type=validate_type)

    return params, returns
