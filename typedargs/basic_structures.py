"""Basic structures used to describe parameters and return values."""

from collections import namedtuple


ParameterInfo = namedtuple("ParameterInfo", ['type_name', 'validators', 'desc'])
ReturnInfo = namedtuple("ReturnInfo", ['type_name', 'formatter', 'is_data', 'desc'])
