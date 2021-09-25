from openfisca_core.commons import deprecated
from openfisca_core.scripts import FindDeprecated


@deprecated(since = "yesterday", expires = "tomorrow")
def function(a: int, b: float) -> float:
    return a + b


def test_find_deprecated(capsys):
    """caca."""

    FindDeprecated()()
    assert "[tests.test_find_deprecated.function:6]" in capsys.readouterr().out
