class NoWaysFoundException(Exception):
    """No ways were found with the provided query.
    """
    pass

class QueryInvalidException(Exception):
    """Query invalid. May be improperly formatted or be None."""

class InvalidArgumentTypeException(Exception):
    """Type incorrectly passed."""

class InvalidStringArgumentException(Exception):
    """The passed string argument is invalid."""