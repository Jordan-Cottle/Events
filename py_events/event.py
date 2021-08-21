""" Module for defining the core Event class. """

import logging
from collections import defaultdict
from typing import Callable, Mapping, List, Type
from uuid import uuid4

from .misc import type_of

Handler = Callable[["Event"], None]


class Event:
    """Represents an event that can be published or subscribed to."""

    _handlers: Mapping[Type["Event"], List[Handler]] = defaultdict(list)

    @classmethod
    def add_handler(cls: Type["Event"], handler: Handler):
        """Register a new handler for this type of event."""

        logging.debug(f"Registering {handler} to {cls}")

        cls._handlers[cls].append(handler)

    @classmethod
    def handler(cls, handler: Handler):
        """Decorator to register a function as a handler."""

        cls.add_handler(handler)

        return handler

    @classmethod
    def remove_handler(cls, handler: Handler):
        """Remove a registered handler."""

        logging.debug(f"Removing {handler} from {cls}")
        cls._handlers[cls].remove(handler)

    def __init__(self, uuid=None) -> None:
        logging.debug(f"{type(self)} created")

        self.uuid = uuid or uuid4()
        self.canceled = False

    @property
    def handlers(self):
        """Recursively retrieve all registered handlers for this event."""
        handlers = []
        for cls in type(self).__mro__:
            if not hasattr(cls, "_handlers"):
                continue

            # This class is using it's own internal interface here
            # pylint: disable=protected-access
            new_handlers = cls._handlers[cls]
            logging.debug(f"Including {new_handlers} from {cls} for {self}")
            handlers.extend(new_handlers)

        return handlers

    def fire(self):
        """Fire this event by sending it to all registered handlers."""

        self.canceled = False
        for handler in self.handlers:
            handler(self)

            if self.canceled:
                break

    def cancel(self):
        """Mark this event as canceled."""

        logging.debug(f"Canceling {self}")
        self.canceled = True

    def __str__(self) -> str:
        return f"{type_of(self)} {self.uuid}"

    def __repr__(self) -> str:
        return f"{type_of(self)}(uuid={self.uuid!r})"
