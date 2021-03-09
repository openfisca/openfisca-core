from sys import exit

from click import group


@group(context_settings = {"help_option_names": ["-h", "--help"]})
def openfisca() -> None:
    pass


@openfisca.command(help = "Run the OpenFisca Web API.")
def serve() -> None:
    pass


@openfisca.command(help = "Run OpenFisca YAML tests.")
def test() -> None:
    pass


if __name__ == "__main__":
    exit(openfisca())
