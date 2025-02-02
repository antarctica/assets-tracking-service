#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.11"
# dependencies = []
# [tool.uv]
# exclude-newer = "2024-12-28T00:00:00Z"
# ///

import argparse
from pathlib import Path

__VERSION__ = "0.3.0"
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


def _write_migration(path: Path, context_path: Path | None = None) -> None:
    if not context_path:
        context_path = path

    number = int(context_path.stem.split("-")[0])
    label = context_path.stem

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        f.write("-- record latest migration\n")
        f.write(
            f"""UPDATE public.meta_migration
SET migration_id = {number}, migration_label = '{label}'
WHERE pk = 1; \n"""  # noqa: S608
        )


def _create_up_migration(path: Path) -> None:
    _write_migration(path)


def _create_down_migration(path: Path) -> None:
    # get path for previous up migration
    up_base_path = path.parent.parent / "up"
    up_number = INIT_DOWN_COUNT - int(path.stem.split("-")[0]) - 1  # previous up migration
    up_path = next(up_base_path.glob(f"{up_number:03}-*.sql"))

    _write_migration(path, up_path)


def _create_migration(name: str) -> tuple[Path, Path]:
    _validate_name(name)
    up_prefix, down_prefix = _calc_next_prefix()

    up_path = MIGRATIONS_ROOT / f"up/{up_prefix}-{name}.sql"
    _create_up_migration(up_path)

    down_path = MIGRATIONS_ROOT / f"down/{down_prefix}-{name}.sql"
    _create_down_migration(down_path)

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
