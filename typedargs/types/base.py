

class BaseInternalType:

    @classmethod
    def FromString(cls, arg):
        """Create an instance of this class from string."""
        raise NotImplementedError

    @classmethod
    def default_formatter(cls, arg):
        """Convert a given instance of this class to string representation."""
        raise NotImplementedError



