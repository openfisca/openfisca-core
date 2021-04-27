# OpenFisca's Python Style Guide

Arguments over code style and formatting are the bread and butter of most open-source projets out there, including OpenFisca.

To avoid this, we have a style guide, that is a set or arbitrary but consistent conventions about how code should be written, for contributors and maintainers alike.

## Notice

### About this style guide

The present style guide is a work in progress.

It largely follows [Python Foundation's](https://www.python.org/dev/peps/pep-0008/), [NumPy's](https://numpydoc.readthedocs.io/en/latest/format.html) and [Google's](https://google.github.io/styleguide/pyguide.html), but it has a lot of her own as well.

### Contributing

Please refer whenever possible to this style guide both for your contributions and your reviews.

If the style in question is not present and contentious, do not hesitate to include an addition to this guide within your proposal or review.

## Imports

1. In general, use import statements for entire namespaces and modules, rather than for classes and functions. Are exempt of this rule the `typing` module, NumPy's `typing` module, and `openfisca_core` module and submodules (but only in the case of class imports).

2. In general, use absolute import statements rather that relative ones. Are exempt of this rule the modules relative to a submodule of OpenFisca, in order to improve the delimitation of internal and external interfaces.

3. Always follow this order for your imports: system modules, third party modules, third party OpenFisca modules, external OpenFisca Core modules, internal OpenFisca Core modules.

For example given:

```
/openfisca_core/axes/__init__.py
/openfisca_core/axes/nothing.py
/openfisca_core/axes/something.py
```

Whenever possible we should expect:

```python
# /openfisca_core/axes/nothing.py
#
# Yes

import copy
import typing
from typing import List

import numpy

from openfisca_country_template import entities

from openfisca_core import tools
from openfisca_core.variables import Variable

from . import Something

if typing.TYPE_CHECKING:
    from numpy.typing import ArrayLike


def do(this: List) -> ArrayLike:
    that = copy.deepcopy(this)
    array = numpy.ndarray(that)
    return Something(entities.Person, Variable)
```

And avoid:

```python
# /openfisca_core/axes/nothing.py
#
# No

from openfisca_country_template.entities import Person
from openfisca_core import variables
from openfisca_core.tools import assert_near
from openfisca_core import axes

from numpy import ndarray
from copy import deepcopy
import typing
import numpy.typing

def do(this: typing.List) -> numpy.typing.ArrayLike:
    that = deepcopy(this)
    array = ndarray(that)
    return axes.Something(Person, variables.Variable)
```
