"""The basic class that is used to store metadata about a function."""

from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
from builtins import range, str
from collections import namedtuple
import inspect
from .exceptions import TypeSystemError, ArgumentError, ValidationError
import typedargs.typeinfo as typeinfo


ParameterInfo = namedtuple("ParameterInfo", ['type_name', 'validators', 'description'])
ReturnInfo = namedtuple("ReturnInfo", ['type_name', 'formatter', 'is_data', 'desc'])


class AnnotatedMetadata(object):
    """All of the associated metadata for an annotated function.

    Args:
        func (callable): The function that we are annotated so that
            we can pull out relevant argument spec information.  If func
            is a class, we pull arguments from its __init__ routine
        name (str): An optional name that will overwrite the default name
            of this function
    """

    def __init__(self, func, name=None):
        self.annotated_params = {}

        if inspect.isclass(func):
            func = func.__init__

        # If we are called to annotate a context, we won't necessarily
        # have any arguments
        try:
            args, varargs, kwargs, defaults = inspect.getargspec(func)

            # Skip self argument if this is a method function
            if len(args) > 0 and args[0] == 'self':
                args = args[1:]

            if defaults is None:
                defaults = []

            self.varargs = varargs
            self.kwargs = kwargs
            self.arg_names = args
            self.arg_defaults = defaults
        except TypeError:
            self.varargs = None
            self.kwargs = None
            self.arg_names = []
            self.arg_defaults = []

        self.return_info = ReturnInfo(None, None, False, None)

        if name is None:
            name = func.__name__

        self.name = name

    def spec_filled(self, pos_args, kw_args):
        """Check if we have enough arguments to call this function.

        Args:
            pos_args (list): A list of all the positional values we have.
            kw_args (dict): A dict of all of the keyword args we have.

        Returns:
            bool: True if we have a filled spec, False otherwise.
        """

        req = [x for x in self.arg_names[:len(self.arg_defaults)] if x not in kw_args]
        return len(req) <= len(pos_args)

    def add_param(self, name, type_name, validators, desc=None):
        """Add type information for a parameter by name.

        Args:
            name (str): The name of the parameter we wish to annotate
            type_name (str): The name of the parameter's type
            validators (list): A list of either strings or n tuples that each
                specify a validator defined for type_name.  If a string is passed,
                the validator is invoked with no extra arguments.  If a tuple is
                passed, the validator will be invoked with the extra arguments.
            desc (str): Optional parameter description.
        """

        if name in self.annotated_params:
            raise TypeSystemError("Annotation specified multiple times for the same parameter", param=name)

        if name not in self.arg_names and name != self.varargs and name != self.kwargs:
            raise TypeSystemError("Annotation specified for unknown parameter", param=name)

        info = ParameterInfo(type_name, validators, desc)
        self.annotated_params[name] = info

    def typed_returnvalue(self, type_name, formatter=None):
        """Add type information to the return value of this function.

        Args:
            type_name (str): The name of the type of the return value.
            formatter (str): An optional name of a formatting function specified
                for the type given in type_name.
        """
        self.return_info = ReturnInfo(type_name, formatter, True, None)

    def string_returnvalue(self):
        """Mark the return value as data that should be converted with str."""
        self.return_info = ReturnInfo(None, str, True, None)

    def custom_returnvalue(self, printer, desc=None):
        """Use a custom function to print the return value.

        Args:
            printer (callable): A function that should take in the return
                value and convert it to a string.
            desc (str): An optional description of the return value.
        """
        self.return_info = ReturnInfo(None, printer, True, desc)

    def has_varargs(self):
        """Check if this function supports variable arguments."""
        return self.varargs is not None

    def has_kwargs(self):
        """Check if this function supports arbitrary keyword arguments."""
        return self.kwargs is not None

    def returns_data(self):
        """Check if this function returns data."""
        return self.return_info.is_data

    def match_shortname(self, name):
        """Try to convert a prefix into a parameter name.

        If the result could be ambiguous or there is no matching
        parameter, throw an ArgumentError

        Args:
            name (str): A prefix for a parameter name

        Returns:
            str: The full matching parameter name
        """

        possible = [x for x in self.arg_names if x.startswith(name)]
        if len(possible) == 0:
            raise ArgumentError("Could not convert short-name full parameter name, none could be found", short_name=name, parameters=self.arg_names)
        elif len(possible) > 1:
            raise ArgumentError("Short-name is ambiguous, could match multiple keyword parameters", short_name=name, possible_matches=possible)

        return possible[0]

    def param_type(self, name):
        """Get the parameter type information by name.

        Args:
            name (str): The full name of a parameter.

        Returns:
            str: The type name or None if no type information is given.
        """

        if name not in self.annotated_params:
            return None

        return self.annotated_params[name].type_name

    def signature(self):
        """Return our function signature as a string."""

        num_args = len(self.arg_names)

        num_def = 0
        if self.arg_defaults is not None:
            num_def = len(self.arg_defaults)

        num_no_def = num_args - num_def

        args = []
        for i in range(0, len(self.arg_names)):
            typestr = ""

            if self.arg_names[i] in self.annotated_params:
                typestr = "{} ".format(self.annotated_params[self.arg_names[i]])

            if i >= num_no_def:
                default = str(self.arg_defaults[i-num_no_def])
                if len(default) == 0:
                    default = "''"

                args.append("{}{}={}".format(typestr, str(self.arg_names[i]), default))
            else:
                args.append(typestr + str(self.arg_names[i]))

        return "{}({})".format(self.name, ", ".join(args))

    def format_returnvalue(self, value):
        """Format the return value of this function as a string.

        Args:
            value (object): The return value that we are supposed to format.

        Returns:
            str: The formatted return value, or None if this function indicates
                that it does not return data
        """

        if not self.return_info.is_data:
            return None

        # If the return value is typed, use the type_system to format it
        if self.return_info.type_name is not None:
            return typeinfo.type_system.format_value(value, self.return_info.type_name, self.return_info.formatter)

        # Otherwise we expect a callable function to convert this value to a string
        return self.return_info.formatter(value)

    def convert_positional_argument(self, index, arg_value):
        """Convert and validate a positional argument.

        Args:
            index (int): The positional index of the argument
            arg_value (object): The value to convert and validate

        Returns:
            object: The converted value.
        """

        arg_name = self.arg_names[index]
        return self.convert_argument(arg_name, arg_value)

    def convert_argument(self, arg_name, arg_value):
        """Given a parameter with type information, convert and validate it.

        Args:
            arg_name (str): The name of the argument to convert and validate
            arg_value (object): The value to convert and validate

        Returns:
            object: The converted value.
        """

        type_name = self.param_type(arg_name)
        if type_name is None:
            return arg_value

        val = typeinfo.type_system.convert_to_type(arg_value, type_name)

        validators = self.annotated_params[arg_name].validators
        if len(validators) == 0:
            return val

        type_obj = typeinfo.type_system.get_type(type_name)

        # Run all of the validators that were defined for this argument.
        # If the validation fails, they will raise an exception that we convert to
        # an instance of ValidationError
        try:
            for validator_name, extra_args in validators:
                if not hasattr(type_obj, validator_name):
                    raise ValidationError("Could not find validator specified for argument", argument=arg_name, validator_name=validator_name, type=str(type_obj), method=dir(type_obj))

                validator = getattr(type_obj, validator_name)
                validator(val, *extra_args)
        except (ValueError, TypeError) as exc:
            raise ValidationError(exc.args[0], argument=arg_name, arg_value=val)

        return val
