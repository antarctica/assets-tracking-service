#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.11"
# dependencies = []
# [tool.uv]
# exclude-newer = "2024-12-28T00:00:00Z"
# ///

import argparse
from pathlib import Path

__VERSION__ = "0.2.0"
PROJECT_ROOT = Path(__file__).resolve().parent.parent
MIGRATIONS_ROOT = PROJECT_ROOT / "src" / "assets_tracking_service" / "resources" / "db_migrations"
INIT_DOWN_COUNT = 1000


def _validate_name(name: str) -> None:
    # name must be alphanumeric plus dashes
    if not name.replace("-", "").isalnum():
        msg = "Name must be alphanumeric plus dashes"
        raise ValueError(msg)


def _calc_next_prefix() -> tuple[str, str]:
    up_files = sorted(MIGRATIONS_ROOT.glob("up/*.sql"))
    try:
        head_prefix = up_files[-1].stem.split("-")[0]
    except IndexError:
        head_prefix = "000"
    next_up_count = int(head_prefix) + 1

    next_up_prefix = str(next_up_count).zfill(3)
    next_down_prefix = str(INIT_DOWN_COUNT - next_up_count).zfill(3)
    return next_up_prefix, next_down_prefix


def _create_migration(name: str) -> tuple[Path, Path]:
    _validate_name(name)
    up_prefix, down_prefix = _calc_next_prefix()

    up_path = MIGRATIONS_ROOT / f"up/{up_prefix}-{name}.sql"
    up_path.parent.mkdir(parents=True, exist_ok=True)
    up_path.touch(exist_ok=False)

    down_path = MIGRATIONS_ROOT / f"down/{down_prefix}-{name}.sql"
    down_path.parent.mkdir(parents=True, exist_ok=True)
    down_path.touch(exist_ok=False)

    return up_path, down_path


def main() -> None:
    """Script entrypoint."""
    parser = argparse.ArgumentParser()
    parser.add_argument("name")
    args = parser.parse_args()

    up_path, down_path = _create_migration(args.name)
    print("Migration created:")
    print(f"- ⬆️ {up_path.resolve()}")
    print(f"- ⬇️ {down_path.resolve()}")


if __name__ == "__main__":
    main()
