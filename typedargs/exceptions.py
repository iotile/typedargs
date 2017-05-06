"""A generic key-value based exception class."""

# This file is adapted from python code released by WellDone International
# under the terms of the LGPLv3.  WellDone International's contact information is
# info@welldone.org
# http://welldone.org
#
# Modifications to this file from the original created at WellDone International
# are copyright Arch Systems Inc.


class KeyValueException(Exception):
    """An exception taking key value pairs containing exception information.

    KeyValueExceptions provide a convenient way to include additional information
    about the source or context of an exception without having to convert it all to
    a formatted string.

    Args:
        msg (string): A short message about the cause of this exception, not including
            its type or any placeholders
        **kwargs: Any named parameters that you would like included with this exception
    """

    def __init__(self, msg, **kwargs):
        self.params = kwargs
        self.msg = msg

        super(KeyValueException, self).__init__()

    def format(self, exclude_class=False):
        """Format this exception as a string including class name.

        Args:
            exclude_class (bool): Whether to exclude the exception class
                name when formatting this exception

        Returns:
            string: a multiline string with the message, class name and
                key value parameters passed to create the exception.
        """

        if exclude_class:
            msg = self.msg
        else:
            msg = "%s: %s" % (self.__class__.__name__, self.msg)

        if len(self.params) != 0:
            paramstring = "\n".join([str(key) + ": " + str(val) for key, val in self.params.iteritems()])
            msg += "\nAdditional Information:\n" + paramstring

        return msg

    def format_msg(self):
        """Format this exception as a string excluding class name.

        Returns:
            string: a multiline string with the message and
                key value parameters passed to create the exception.
        """

        return self.format(exclude_class=True)

    def to_dict(self):
        """Convert this exception to a dictionary.

        Returns:
            dist: A dictionary of information about this exception,
                Has a 'reason' key, a 'type' key  and a dictionary of params
        """

        out = {}
        out['reason'] = self.msg
        out['type'] = self.__class__.__name__
        out['params'] = self.params

        return out

    def __str__(self):
        return self.format()


class ValidationError(KeyValueException):
    """
    API routines can impose validation criteria on` their arguments in
    addition to requiring simply a certain type of argument.  A clasic
    example is the "path" type which can have validators like "readable"
    or "exists".  When validation fails, this error is thrown.
    """

    pass


class ConversionError(KeyValueException):
    """
    All API functions take typed parameters.  Each type defines conversion
    operators for python types that are logically related to it.  When no
    valid conversion exists for the data type passed, this error is thrown.
    """

    pass


class NotFoundError(KeyValueException):
    """
    Thrown when an attempt to execute an API method is made and the API
    method does not exist.
    """

    pass


class TypeSystemError(KeyValueException):
    """
    There was an error with the IOTile type system.  This can be due to improperly
    specifying an unknown type or because the required type was not properly loaded
    from an external module before a function that used that type was needed.
    """

    pass
