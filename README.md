# Events
A simple event system for using as a component in larger systems.

Inspired by [C# events](https://docs.microsoft.com/en-us/dotnet/csharp/programming-guide/events/).

## Getting Started

This library provides a mechanism to subscribe to and publish events. The primary use case is to enable code that processes events to be separated from the code that generated or detects them.

One common use case would be in implementing a statistics tracker for a game. You would not want to classes/modules responsible for managing the game logic (like a player's HP or calculating combat damage) to be polluted with dozens (or hundreds) or lines of counter incrementing logic (or even worse, user interface updates for those statistics). With this library you could simply fire an event from relevant places and let a dedicated statistics management module/component handle logging, saving, presenting and forwarding statistics about what happened.

Organized properly, using events can allow for a much greater separation of concerns and simplify otherwise complex logic dramatically.

### Installation

Activate your virtual environment if you are using one (and you should be), then execute:
```
python -m pip install py-events
```

### Define your event

The core of this library is the `Event` class. The primary use of `Event` is to subclass it to define a new type of event. Typically, a subclass of `Event` only needs to override the `__init__` method to set up any new attributes that you want the event to have.


#### Define a custom event
```python
from py_events import Event
class CustomEvent(Event):
    """ My custom event. """

    def __init__(self, message:str):
        """This event contains a message to be sent to handlers."""

        super().__init__()

        self.message = message
```


### Set up a handler

Once you have an `Event` subclass defined, you can create a `subscriber` for the event. A `subscriber` is a callable that accepts the event being fired as it's only positional argument. Typically this is a plain function, but can be a class with a `__call__` method defined for more complex use cases.

Registering your `subscriber` can be done in two ways. For simple functions you define directly in your application's source code there is the `Event.handles` method you can use as a decorator to register the function automatically. If you are importing the function from somewhere, or using a callable class instead, you can call the `Event.add_handler` method to register an already constructed callable.

#### Simple handler
```python
import logging

from my_module import CustomEvent

@CustomEvent.handler
def simple_handler(event: CustomEvent) -> None:
    """ Log the message from my custom event. """

    logging.info(event.message)
```

#### Class based handler
```python
import logging

from my_module import CustomEvent

class ComplexHandler:
    """ Log message from custom event and keep track of number of events fired. """

    def __init__(self) -> None:
        self.events_handled_count = 0

    def __call__(self, event:CustomEvent) -> None:
        """ Log message from event and increment events_handled counter. """

        logging.info(event.message)

        self.events_handled_count += 1

# Create a constant reference that other modules could import and use to check on the counter
COMPLEX_HANDLER = ComplexHandler()

CustomEvent.add_handler(COMPLEX_HANDLER)
```


### Publish your event

Once you have a `subscriber` set up you can publish events from anywhere to have them sent to all of the `subscribers` you have set up. Firing an event is as simple as constructing an instance of it and calling it's `fire` method.

> **Useful Note**: The base `Event` class is set up to be relatively stateless, so a single instance of an `Event` can be fired multiple times.

#### Fire your event
```python
from my_module import CustomEvent

CustomEvent("Hello world").fire()
```


