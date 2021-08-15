""" Test module for the base event module. """

import logging
from typing import List, Union
from unittest.mock import patch

import pytest

from py_events import Event
from py_events.misc import type_of


class CustomEvent(Event):
    """Custom event class for testing."""

    TEST_MESSAGE = "Hello World"

    def __init__(self, message, trigger_cancel=False):
        """
        Set trigger_cancel=True to instruct the custom_handler to cancel this event.
        """
        super().__init__()
        self.message = message
        self.trigger_cancel = trigger_cancel


class EventHandler:
    """Event handler for base Events

    Tracks events seen and how many times it has been called.
    """

    def __init__(self) -> None:
        self.events_processed: List[Event] = []

    @property
    def last_event(self) -> Union[Event, None]:
        """Get most recent event seen."""

        return self.events_processed[-1] if self.events_processed else None

    @property
    def call_count(self) -> int:
        """Get number of events this handler has processed."""

        return len(self.events_processed)

    def __call__(self, event: Event) -> None:
        logging.debug(f"{self} handling {event}")
        assert event is not None

        self.events_processed.append(event)

    def __str__(self) -> str:
        return type_of(self)


class CustomHandler(EventHandler):
    """Custom even handler for tests.

    If event.trigger_cancel is True the event is canceled.
    Otherwise basic information about it is processed and the
    event is tracked.
    """

    def __call__(self, event: Event) -> None:

        super().__call__(event)

        assert isinstance(event, CustomEvent)
        assert event.message == CustomEvent.TEST_MESSAGE

        if event.trigger_cancel:
            event.cancel()


@pytest.fixture(name="event_handler")
def create_event_handler():
    """Initialize a fresh event handler for testing with."""

    return EventHandler()


@pytest.fixture(name="custom_handler")
def create_custom_event_handler():
    """Initialize a fresh custom event handler for testing with."""

    return CustomHandler()


@pytest.fixture(autouse=True)
def clear_event_handlers():
    """Cleanup event handlers for Event class after each test."""
    # This fixture performs "low-level" cleanup of registered event handlers to isolate tests
    # that isn't part of any public interface the Event class provides
    # pylint: disable=protected-access

    assert len(Event().handlers) == 0

    yield

    Event._handlers.clear()


def test_base_event(event_handler: EventHandler):
    """Test base class for events can be regsitered and fired."""

    event = Event()
    event.fire()

    assert event_handler.last_event is None
    assert event_handler.call_count == 0

    Event.add_handler(event_handler)
    assert event.handlers == [event_handler]

    event.fire()
    assert event_handler.last_event is event
    assert event_handler.call_count == 1

    Event.remove_handler(event_handler)
    assert event.handlers == []

    event.fire()
    assert event_handler.last_event is event
    assert event_handler.call_count == 1


def test_event_handler_decorator():
    """Test event handlers can be registered via decorator."""

    event = Event()

    @Event.handler
    def handler(_event: Event):
        assert _event is event

        handler.call_count += 1

    handler.call_count = 0

    assert event.handlers == [handler]

    event.fire()
    assert handler.call_count == 1

    Event.remove_handler(handler)

    assert event.handlers == []


def test_subclassing_event(event_handler: EventHandler, custom_handler: CustomHandler):
    """Ensure subclasses of Event behave as expected."""

    custom_event = CustomEvent(CustomEvent.TEST_MESSAGE)
    assert custom_event.handlers == []

    CustomEvent.add_handler(custom_handler)

    assert custom_event.handlers == [custom_handler]

    custom_event.fire()
    assert event_handler.call_count == 0
    assert event_handler.last_event is None
    assert custom_handler.call_count == 1
    assert custom_handler.last_event is custom_event

    Event.add_handler(event_handler)

    second_custom_event = CustomEvent(CustomEvent.TEST_MESSAGE)
    second_custom_event.fire()

    assert event_handler.call_count == 1
    assert event_handler.last_event is second_custom_event
    assert custom_handler.call_count == 2
    assert custom_handler.events_processed == [custom_event, second_custom_event]


def test_canceling_event(event_handler: EventHandler, custom_handler: CustomHandler):
    """Verify that canceling an event stops less-specific handlers from being called"""

    Event.add_handler(event_handler)
    CustomEvent.add_handler(custom_handler)

    custom_event = CustomEvent(CustomEvent.TEST_MESSAGE, trigger_cancel=True)
    assert custom_event.handlers == [custom_handler, event_handler]

    custom_event.fire()
    assert custom_event.canceled

    assert custom_handler.call_count == 1
    assert custom_handler.last_event is custom_event

    assert event_handler.call_count == 0
    assert event_handler.last_event is None


def test_repeat_fire_of_canceled_events(
    event_handler: EventHandler, custom_handler: CustomHandler
):
    """Verify that re-firing a canceled event still works."""

    Event.add_handler(event_handler)
    CustomEvent.add_handler(custom_handler)

    custom_event = CustomEvent(CustomEvent.TEST_MESSAGE, trigger_cancel=True)

    custom_event.fire()
    assert custom_event.canceled

    assert custom_handler.call_count == 1
    assert custom_handler.last_event is custom_event

    custom_event.fire()
    assert custom_handler.call_count == 2
    assert custom_handler.events_processed == [custom_event, custom_event]

    assert event_handler.call_count == 0
    assert event_handler.last_event is None


def test_event_with_provided_uuid():
    """Verify that passing in a uuid for an event instance skips generating one."""

    pre_computed_uuid = "1234"

    with patch("py_events.event.uuid4") as uuid_mock:
        event = Event(uuid=pre_computed_uuid)

    uuid_mock.assert_not_called()
    assert event.uuid == pre_computed_uuid
