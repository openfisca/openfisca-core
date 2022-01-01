from __future__ import annotations

import os
import warnings
import yaml  # noqa: F401

from openfisca_core.warnings import LibYAMLWarning

try:
    from yaml import CLoader as Loader

except ImportError:
    message = [
        "libyaml is not installed in your environment.",
        "This can make OpenFisca slower to start,",
        "and your test suite slower to run.",
        "Once you have installed libyaml,",
        "run 'pip uninstall pyyaml && pip install pyyaml --no-cache-dir'",
        "so that it is used by your Python environment.",
        os.linesep,
        ]
    warnings.warn(" ".join(message), LibYAMLWarning)

    # see https://github.com/python/mypy/issues/1153#issuecomment-455802270
    from yaml import SafeLoader as Loader  # type: ignore # noqa: F401
