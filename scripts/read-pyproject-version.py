#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.11"
# [tool.uv]
# exclude-newer = "2024-12-28T00:00:00Z"
# ///

import tomllib
from pathlib import Path


def _read_pyproject_version() -> str:
    with Path("pyproject.toml").open(mode="rb") as f:
        data = tomllib.load(f)

    return data["project"]["version"]


def main() -> None:
    """Read the version from pyproject.toml."""
    print(_read_pyproject_version())


if __name__ == "__main__":
    main()
