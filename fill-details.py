r""" Script to automatically fill project data. """

import os
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
import re
from typing import Any, TypedDict


@contextmanager
def prompt(msg: str) -> Iterator[Any]:
    r""" A context manager to perform actions with prompts. """
    print(msg+"...", end="")
    try:
        yield
        print(" done.")
    except Exception as e:
        print("")
        raise e


class ProjectData(TypedDict, total=True):
    r""" Data for a project. """

    PROJECT_NAME: str
    PACKAGE_NAME: str
    PROJECT_DESCRIPTION: str


def replace_text(data: ProjectData, text: str) -> str:
    r""" Replaces placeholders with corresponding project data in a piece of text. """
    for k, v in data.items():
        text = text.replace(k, str(v))
    return text


def fill_data(data: ProjectData, filenames: Sequence[str], include_scripts: bool) -> None:
    r""" Replaces placeholders with corresponding project data in the given filenames, then in the file text. """

    with prompt("Renaming package folder"):
        os.rename("./PACKAGE_NAME/", f"./{PACKAGE_NAME}/")
    if not include_scripts:
        with prompt(f"Removing ./{PACKAGE_NAME}/scripts.py"):
            os.remove(f"./{PACKAGE_NAME}/scripts.py")
        with prompt(f"Removing from 'include_modules' of 'make-api.json'"):
            with open("docs/make-api.json", "r", encoding="utf-8") as f:
                text = f.read()
                text = text.replace(r"""
        "PACKAGE_NAME.SCRIPT_MODULE_NAME"
    """, "")
            with open("docs/make-api.json", "w", encoding="utf-8") as f:
                f.write(text)
    with prompt("Replacing placeholders in filenames"):
        filenames = tuple(replace_text(data, filename) for filename in filenames if include_scripts or filename != "PACKAGE_NAME/scripts.py")
    for filename in filenames:
        with prompt(f"Replacing placeholders in {repr(filename)}"):
            with open(filename, "r", encoding="utf-8") as f:
                text = f.read()
            text = replace_text(data, text)
            if filename == "setup.cfg":
                script_cfg = f"[options.entry_points]\nconsole_scripts =\n    TEST_COMMAND={PACKAGE_NAME}.scripts:TEST_COMMAND_FUN\n"
                assert script_cfg in text, text
                text = text.replace(script_cfg, "")
            if filename == "docs/api-toc.rst":
                script_toc_line = f"    api/{PACKAGE_NAME}.SCRIPT_MODULE_NAME\n"
                assert script_toc_line in text, text
                text = text.replace(script_toc_line, "")
            if filename == "README.rst":
                while "BEGIN_TO_REMOVE" in text:
                    assert "END_TO_REMOVE" in text, text
                    start = text.index("BEGIN_TO_REMOVE")
                    end = text.index("END_TO_REMOVE")
                    text = text[:start]+text[end+len("END_TO_REMOVE"):]
                assert "END_TO_REMOVE" not in text, text
            with open(filename, "w", encoding="utf-8") as f:
                f.write(text)


def valid_project_data(data: ProjectData) -> bool:
    r""" Validates project data. """
    PROJECT_NAME = data["PROJECT_NAME"]
    PACKAGE_NAME = data["PACKAGE_NAME"]
    # PROJECT_DESCRIPTION = data["PROJECT_DESCRIPTION"]
    if not re.fullmatch("[a-zA-Z][a-zA-Z0-9_]*", PACKAGE_NAME):
        print(f"Invalid PACKAGE_NAME = {PACKAGE_NAME}")
        return False
    if not re.fullmatch("[a-zA-Z][a-zA-Z0-9_-]*", PROJECT_NAME):
        print(f"Invalid PROJECT_NAME = {PROJECT_NAME}")
        return False
    return True


filenames = (
    "README.rst",
    "CONTRIBUTING.md",
    "SECURITY.md",
    "run-tests.bat",
    "run-black.bat",
    "setup.cfg",
    "tox.ini",
    ".github/workflows/python-pytest.yml",
    "docs/conf.py",
    "docs/make-api.json",
    "docs/index.rst",
    "docs/api-toc.rst",
    "docs/getting-started.rst",
    "PACKAGE_NAME/__init__.py",
    "PACKAGE_NAME/scripts.py"
)

if __name__ == "__main__":
    PROJECT_NAME = input("Project name? ").strip()
    PACKAGE_NAME = input("Package name? ").strip()
    PROJECT_DESCRIPTION = input("Project description? ").strip()
    include_scripts = input("Include scripts (Y/n)? ").upper().startswith("Y")
    data: ProjectData = dict(PROJECT_NAME=PROJECT_NAME, PACKAGE_NAME=PACKAGE_NAME, PROJECT_DESCRIPTION=PROJECT_DESCRIPTION)
    if valid_project_data(data):
        print("About to replace placeholders with the following project data:")
        for k, v in data.items():
            print(f"  {k} = {v}")
        print(f"  Include scripts: {'yes' if include_scripts else 'no'}")
        confirmed = input("Confirm (Y/n)? ").upper().startswith("Y")
        if confirmed:
            fill_data(data, filenames, include_scripts)
            print("Done.")
