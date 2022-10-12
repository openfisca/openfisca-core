import warnings
import os
import yaml
import typing
from policyengine_core.warnings import LibYAMLWarning


try:
    from yaml import CLoader as Loader
except ImportError:
    message = [
        "libyaml is not installed in your environment.",
        "This can make OpenFisca slower to start.",
        "Once you have installed libyaml, run 'pip uninstall pyyaml && pip install pyyaml --no-cache-dir'",
        "so that it is used in your Python environment." + os.linesep,
    ]
    warnings.warn(" ".join(message), LibYAMLWarning)
    from yaml import Loader  # type: ignore # (see https://github.com/python/mypy/issues/1153#issuecomment-455802270)

ALLOWED_PARAM_TYPES = (float, int, bool, type(None), typing.List)
COMMON_KEYS = {"description", "metadata", "documentation"}
FILE_EXTENSIONS = {".yaml", ".yml"}


def date_constructor(_loader, node):
    return node.value


yaml.add_constructor(
    "tag:yaml.org,2002:timestamp", date_constructor, Loader=Loader
)


def dict_no_duplicate_constructor(loader, node, deep=False):
    keys = [key.value for key, value in node.value]

    if len(keys) != len(set(keys)):
        duplicate = next((key for key in keys if keys.count(key) > 1))
        raise yaml.parser.ParserError(
            "", node.start_mark, f"Found duplicate key '{duplicate}'"
        )

    return loader.construct_mapping(node, deep)


yaml.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    dict_no_duplicate_constructor,
    Loader=Loader,
)
