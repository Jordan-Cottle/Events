""" Event package for managing event handling.

The primary use case is to subclass the `Event` class to create new types fo events.

Anywhere that needs to fire or listen for events can use the subclass to do so.
Event publishers and subscribers do not need to know about each other.
The `Event` class handles routing messages from the publisher to any and all subscribers.
"""

from .event import Event, Handler
