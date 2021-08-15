#! /usr/bin/env python
""" Scripts for development """

from typing import Iterable
from subprocess import run

from argparse import ArgumentParser

SOURCE_CODE_LOCATIONS = " ".join(["py_events", "tests", __file__])


def _run(command):
    print(command)
    return run(command, check=True)


def run_black(options: Iterable[str] = ("--check", "--diff")) -> None:
    """Execute black on all source code in project."""

    _run(f"black {' '.join(options)} {SOURCE_CODE_LOCATIONS}")


def run_pylint(options: Iterable[str] = ()) -> None:
    """Execute pylint on all source code in project."""

    _run(f"pylint {' '.join(options)} {SOURCE_CODE_LOCATIONS}")


def run_mypy(options: Iterable[str] = ()) -> None:
    """Execute mypy for all source code in project."""

    _run(f"mypy {' '.join(options)} {SOURCE_CODE_LOCATIONS}")


def check(tools: Iterable[str] = ("black", "mypy", "pylint")) -> None:
    """Check source code using static analysis"""

    static_analysis_tools = {
        "black": run_black,
        "pylint": run_pylint,
        "mypy": run_mypy,
    }

    for tool in tools:
        static_analysis_tools[tool]()


def test(options: Iterable[str] = ()) -> None:
    """Run all pytest."""

    _run(f"pytest {' '.join(options)}")


COMMANDS = {
    "check": check,
    "black": run_black,
    "pylint": run_pylint,
    "mypy": run_mypy,
    "test": test,
}

if __name__ == "__main__":
    parser = ArgumentParser(description="Local development scripts")

    parser.add_argument("command", help="command to check", choices=COMMANDS)

    args = parser.parse_args()

    print(args.command)

    COMMANDS[args.command]()
