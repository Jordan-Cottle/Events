""" Module for miscellaneous utilities. """


from typing import Any


def type_of(obj: Any) -> str:
    """Get class name of an object as a string."""

    return type(obj).__qualname__
