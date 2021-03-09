from sys import exit

from click import group

from openfisca_core.scripts.openfisca_command import get_parser
from openfisca_web_api.scripts.serve import main as run_serve


@group(context_settings = {"help_option_names": ["-h", "--help"]})
def openfisca() -> None:
    pass


@openfisca.command(help = "Run the OpenFisca Web API.")
def serve() -> None:
    exit(run_serve(get_parser()))


@openfisca.command(help = "Run OpenFisca YAML tests.")
def test() -> None:
    pass


if __name__ == "__main__":
    exit(openfisca())
