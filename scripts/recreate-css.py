# This script must run using a Python interpreter with the `assets_tracking_service` package installed.

import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory

from jinja2 import Environment, PackageLoader, select_autoescape

from assets_tracking_service.config import Config


def dumps_css(export_path: Path, tw_cli_path: Path) -> None:
    """
    Generate site styles.

    Note: This script should only be run after static site content has been generated.

    Steps:
    1. generates a source CSS file from a Jinja2 template (to dynamically set the path to the output site)
    2. run the Tailwind CLI to generate an output CSS file with CSS any classes used across the output site

    After running, the static site needs regenerating to copy the output CSS file into the output site.
    """
    _loader = PackageLoader("assets_tracking_service.lib.bas_data_catalogue", "resources/css")
    _jinja = Environment(loader=_loader, autoescape=select_autoescape(), trim_blocks=True, lstrip_blocks=True)
    src_css = _jinja.get_template("main.css.j2").render(site_path=export_path.resolve())
    dst_path = Path("src/assets_tracking_service/lib/bas_data_catalogue/resources/css/main.css")

    with TemporaryDirectory() as tmp_dir:
        src_path = Path(tmp_dir) / "main.src.css"
        with src_path.open("w") as src_file:
            src_file.write(src_css)

        subprocess.run(  # noqa: S603
            [tw_cli_path, "-i", str(src_path.resolve()), "-o", str(dst_path.resolve())],
            check=True,
        )
    print(f"CSS generated as '{dst_path.resolve()}'")


def main() -> None:
    """Entrypoint."""
    config = Config()
    dumps_css(
        export_path=config.EXPORTER_DATA_CATALOGUE_OUTPUT_PATH,
        tw_cli_path=Path("./scripts/tailwind"),
    )


if __name__ == "__main__":
    main()
