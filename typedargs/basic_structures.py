"""Basic structures used to describe parameters and return values."""
from typing import Optional


class ParameterInfo:
    """
    Args:
        type_class: class of parameter value type
        type_name: parameter type name
        validators: list of validators
        desc: parameter description
    """
    def __init__(self, type_class: Optional[type], type_name: Optional[str], validators: Optional[list], desc: Optional[str]):

        self.type_class = type_class
        self.type_name = type_name
        self.validators = validators
        self.desc = desc

    def __eq__(self, other):
        return tuple(self) == other

    def __iter__(self):
        for prop in (self.type_class, self.type_name, self.validators, self.desc):
            yield prop

    def __str__(self):
        return str(tuple(self))

    def __repr__(self):
        return '<{} type_class={}, type_name={}, validators={}, desc={}>' \
               ''.format(self.__class__.__name__, self.type_class, self.type_name, self.validators, self.desc)


class ReturnInfo:
    """
    Args:
        type_class: class of parameter value type
        type_name: parameter type name
        formatter: parameter string formatter name
        is_data: True if annotated function returns any data
        desc: parameter description
    """
    def __init__(self, type_class: Optional[type], type_name: Optional[str], formatter: Optional[tuple], is_data: Optional[bool], desc: Optional[str]):

        self.type_class = type_class
        self.type_name = type_name
        self.formatter = formatter
        self.is_data = is_data
        self.desc = desc

    def __eq__(self, other):
        return tuple(self) == other

    def __iter__(self):
        for prop in (self.type_class, self.type_name, self.formatter, self.is_data, self.desc):
            yield prop

    def __str__(self):
        return str(tuple(self))

    def __repr__(self):
        return '<{} type_class={}, type_name={}, formatter={}, is_data={}, desc={}>'.format(
            self.__class__.__name__, self.type_class, self.type_name, self.formatter, self.is_data, self.desc)
