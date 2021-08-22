#! /usr/bin/env python
""" Scripts for development """

import json
import os
import re
from argparse import ArgumentParser
from http import HTTPStatus
from subprocess import PIPE, CalledProcessError, run
from typing import Callable, Iterable, Mapping
from urllib.error import HTTPError
from urllib.parse import urlparse
from urllib.request import urlopen

SOURCE_CODE_LOCATIONS = " ".join(["py_events", "tests", __file__])
PYPI = os.getenv("PYPI", "pypi")
PROJECT_NAME = "py-events"

assert (
    os.getenv("VIRTUAL_ENV") is not None
), "You really should be using a virtual environment"


def _run(command):
    print(command)

    try:
        output = run(command, check=True, shell=True, text=True, stdout=PIPE).stdout
    except CalledProcessError as error:
        print(error.stdout)
        raise

    print(output)
    return output.strip()


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


def get_git_tag():
    """Get the git tag for this commit.

    It's a bit of a mess with all of the possible different ways actions can check out the project.
    """

    git_ref = os.getenv("GITHUB_REF")

    # Use passed in git reference
    if git_ref is not None:
        git_tag = git_ref.split("/")[-1]
        if re.match(r"v\d+.\d+.\d+", git_tag):
            return git_tag

    # This enables the git describe command below to work since by default the information
    # required by `git describe` is not checkout out within the actions environment
    try:
        _run("git fetch --prune --unshallow")
    except CalledProcessError as error:
        # If we didn't need this, then ignore the error
        if error.returncode != 128:
            raise

    return _run("git describe --abbrev=0")


def check_version() -> None:
    """Assert that the latest git tag matches the poetry version."""

    current_version = _run("poetry version -s")
    print(f"Latest version: {current_version}")

    git_tag = get_git_tag()
    if git_tag != f"v{current_version}":
        raise ValueError(
            f"Git tag ({git_tag}) does not match poetry version ({current_version})"
        )


def publish() -> None:
    """Publish to pypi if there is a new version.

    Authentication for publishing needs to be configured beforehand.
    """

    check_version()

    if PYPI != "pypi":
        scheme, net_location, *_ = urlparse(
            _run(f"poetry config repositories.{PYPI}.url")
        )
        pypi_host = f"{scheme}://{net_location}"
    else:
        pypi_host = "https://pypi.org/"

    try:
        with urlopen(f"{pypi_host}/pypi/{PROJECT_NAME}/json") as response:
            meta_data = json.loads(response.read())
            latest_published_version = meta_data["info"]["version"].strip()
    except HTTPError as error:
        if error.code == HTTPStatus.NOT_FOUND:
            latest_published_version = None
        else:
            raise

    print(
        f"Latest version of {PROJECT_NAME} on {pypi_host}: '{latest_published_version}'"
    )

    current_version = _run("poetry version -s")
    print(f"Current version of {PROJECT_NAME} is '{current_version}'")

    if current_version == latest_published_version:
        print(f"{pypi_host} has the most recent version, no publish required")
        return

    print(f"Newer version of {PROJECT_NAME} detected.")
    if PYPI != "pypi":
        _run(f"poetry publish -n -r {PYPI}")
    else:
        _run("poetry publish -n")


COMMANDS: Mapping[str, Callable] = {
    "check": check,
    "black": run_black,
    "pylint": run_pylint,
    "mypy": run_mypy,
    "test": test,
    "check_version": check_version,
    "publish": publish,
}

if __name__ == "__main__":
    parser = ArgumentParser(description="Local development scripts")

    parser.add_argument("command", help="command to check", choices=COMMANDS)

    args = parser.parse_args()

    print(args.command)

    COMMANDS[args.command]()
