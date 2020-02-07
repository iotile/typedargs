"""Basic structures used to describe parameters and return values."""


class ParameterInfo:

    def __init__(self, type_class, type_name, validators, desc):
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


class ReturnInfo:

    def __init__(self, type_class, type_name, formatter, is_data, desc):
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
