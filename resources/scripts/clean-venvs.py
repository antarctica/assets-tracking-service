from pathlib import Path
from shutil import rmtree

__VERSION__ = "0.1.0"
VENVS_ROOT = Path("/data/magic/.venv")
STAGING_MODULE_PATH = Path("/data/magic/.Modules/modulefiles/assets-tracking-service/0.0.0.STAGING")
PROJECT = "assets-tracking-service"


def _find_prerelease_venvs(project: str) -> list[Path]:
    return list(VENVS_ROOT.glob(f"{project}-*post*"))


def _get_staging_module_venv(module_path: Path) -> Path:
    with module_path.open() as f:
        for line in f:
            if line.startswith("set basedir"):
                # for `set basedir "/data/magic/.venv/assets-tracking-service-0-0-0-post42"` get the path
                return Path(line.split(" ")[2].replace('"', "").strip())

    msg = "Could not find basedir in module file"
    raise ValueError(msg)


def main() -> None:
    """Script entrypoint."""
    project_venvs = _find_prerelease_venvs(PROJECT)
    staging_venv = _get_staging_module_venv(STAGING_MODULE_PATH)
    filtered_venvs = [venv for venv in project_venvs if venv.resolve() != staging_venv.resolve()]

    print(f"Found {len(project_venvs)} venvs:")
    for venv in project_venvs:
        print(f"- {venv.resolve()}")
    print(f"Staging venv: {staging_venv.resolve()}")
    print(f"Filtered venvs (excluding staging venv): {len(filtered_venvs)}")
    for venv in filtered_venvs:
        print(f"- {venv.resolve()}")

    # confirm deletion
    print("Do you want to delete these venvs? [y/N]")
    if input().lower() != "y":
        print("Aborting")
        return
    for venv in filtered_venvs:
        print(f"Deleting {venv.resolve()}")
        rmtree(venv)


if __name__ == "__main__":
    main()
