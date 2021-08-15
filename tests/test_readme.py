""" This test module does some python voodoo to import and execute the code examples in the readme.

I don't like documentation that gets out of date, and this was a fun/magic way to ensure the readme
stays accurate.
"""
import re
import sys
from types import ModuleType
from importlib import import_module
from unittest.mock import patch

import pytest

from py_events.misc import type_of

PYTHON_BLOCK_RE = "\n```python(([^`]|\n)*)"
CUSTOM_EVENT_PATTERN = re.compile(f"#### Define a custom event{PYTHON_BLOCK_RE}")
SIMPLE_HANDLER_PATTERN = re.compile(f"#### Simple handler{PYTHON_BLOCK_RE}")
COMPLEX_HANDLER_PATTERN = re.compile(f"#### Class based handler{PYTHON_BLOCK_RE}")
FIRE_EVENT_PATTERN = re.compile(f"#### Fire your event{PYTHON_BLOCK_RE}")

with open("README.md") as readme:
    README = readme.read()


def compile_and_install_module(module_name, readme_regex) -> ModuleType:
    """Load source code from readme and install it.

    Uses `readme_regex` to locate source and installs it under `module_name`.

    End result is that `import <module_name>` should work.
    """
    module = ModuleType(module_name, "Module created from source code in readme")

    # Retrieve block of source code for CustomEvent
    match = re.search(readme_regex, README)
    assert match, f"Source code block for {module_name} not found"

    source_block = match.group(1)

    # Execute source in context of empty/fake module
    exec(source_block, module.__dict__)  # pylint: disable=exec-used
    # Yes pylint, I know this is dangerous. But we're executing code
    # that is checked into the repository on the machine that it is checked in to
    # If someone writes malicious code into the readme and runs it on their own
    # machine. It's their own fault for writing and then running the bad code

    # Insert fake module into sys.modules. It's now a "real" module
    sys.modules[module_name] = module

    # Imports should work now
    return import_module(module_name)


@pytest.fixture(name="my_module", scope="session")
def compile_and_install_my_module_from_readme() -> ModuleType:
    """Extracts and compiles source code from readme."""

    module_name = "my_module"
    return compile_and_install_module(module_name, CUSTOM_EVENT_PATTERN)


@pytest.fixture(name="simple_handler", scope="session")
def compile_and_install_simple_handler(my_module) -> ModuleType:
    """Extract and compile simple handler code from readme."""

    # This will more likely fail with an attribute error than on the None check
    assert my_module.CustomEvent is not None

    module_name = "simple_handler"
    return compile_and_install_module(module_name, SIMPLE_HANDLER_PATTERN)


@pytest.fixture(name="complex_handler", scope="session")
def compile_and_install_complex_handler(my_module) -> ModuleType:
    """Extract and compile simple handler code from readme."""

    # This will more likely fail with an attribute error than on the None check
    assert my_module.CustomEvent is not None

    module_name = "complex_handler"
    return compile_and_install_module(module_name, COMPLEX_HANDLER_PATTERN)


@pytest.fixture(name="CustomEvent")
def import_custom_event(my_module):
    """Import CustomEvent from my_module."""

    return my_module.CustomEvent


def test_simple_handler_from_readme_works(simple_handler, CustomEvent):
    """Ensure simple handler from readme works as intended"""

    # This will more likely fail with an attribute error than on the type check
    assert type_of(simple_handler.simple_handler) == "function"

    test_message = "Hello world"

    custom_event = CustomEvent(test_message)

    with patch("simple_handler.logging") as logging_mock:
        custom_event.fire()

    logging_mock.info.assert_called_once()
    logging_mock.info.assert_called_with(test_message)


def test_complex_handler_from_readme_works(complex_handler, CustomEvent):
    """Ensure that the complex handler example from readme works."""

    # This will more likely fail with an attribute error than on the type check
    assert type_of(complex_handler.ComplexHandler) == "type"

    test_message = "Hello world"

    custom_event = CustomEvent(test_message)

    with patch("complex_handler.logging") as logging_mock:
        custom_event.fire()

    logging_mock.info.assert_called_once()
    logging_mock.info.assert_called_with(test_message)

    assert complex_handler.COMPLEX_HANDLER.events_handled_count == 1


def test_event_fire_example_from_readme_works_with_simple_handler(simple_handler):
    """Ensure the firing event example works with the siple handler"""

    # This will more likely fail with an attribute error than on the type check
    assert type_of(simple_handler.simple_handler) == "function"

    with patch("simple_handler.logging") as logging_mock:
        compile_and_install_module("main", FIRE_EVENT_PATTERN)

    logging_mock.info.assert_called_once()
    logging_mock.info.assert_called_with("Hello world")


def test_event_fire_example_from_readme_works_with_complex_handler(complex_handler):
    """Ensure the firing event example works with the siple handler"""

    # This will more likely fail with an attribute error than on the type check
    assert type_of(complex_handler.ComplexHandler) == "type"

    with patch("simple_handler.logging") as logging_mock:
        compile_and_install_module("main", FIRE_EVENT_PATTERN)

    logging_mock.info.assert_called_once()
    logging_mock.info.assert_called_with("Hello world")
