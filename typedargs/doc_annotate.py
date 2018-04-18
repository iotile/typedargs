"""Routines for extracting parmeter and return information from a docstring."""

from __future__ import (unicode_literals, print_function, absolute_import)
from builtins import str
import inspect
from .doc_parser import parse_param, parse_return


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
