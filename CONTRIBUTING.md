Thank you for wanting to contribute to OpenFisca! :smiley:

TL;DR: [GitHub Flow](https://guides.github.com/introduction/flow/), [SemVer](http://semver.org/), sweat on naming and messages.


## Pull requests

We follow the [GitHub Flow](https://guides.github.com/introduction/flow/): all code contributions are submitted via a pull request towards the `master` branch.

Opening a Pull Request means you want that code to be merged. If you want to only discuss it, send a link to your branch along with your questions through whichever communication channel you prefer.

### Peer reviews

All pull requests must be reviewed by someone else than their original author.

> In case of a lack of available reviewers, one may review oneself, but only after at least 24 hours have passed without working on the code to review.

To help reviewers, make sure to add to your PR a **clear text explanation** of your changes.

In case of breaking changes, you **must** give details about what features were deprecated.

> You must also provide guidelines to help users adapt their code to be compatible with the new version of the package.


## Advertising changes

### Version number

We follow the [semantic versioning](http://semver.org/) spec: any change impacts the version number, and the version number conveys API compatibility information **only**.

Examples:

#### Patch bump

- Internal optimization (such as cache) with no consequence on the API.

#### Minor bump

- Adding a helper.

#### Major bump

- Renaming or deprecating a helper.
- Changing the behaviour when a legislation parameter doesn't exist at the required date.


### Changelog

Document all changes in the `CHANGELOG.md` file, following the examples already there.


## Error messages

OpenFisca-Core provides an engine for both developers and law experts. The error messages we expose are part of our public API, and should be of high quality so that they help our users fix their problems on their own, and learn how to avoid them in the future.

### Great error messages

We strive to deliver great error messages, which means they are:

- **Clear**: we tell precisely what caused them and why this is a problem.
- **Gentle**: we consider the error to be caused by legitimate ambiguity. Otherwise, it wouldn't need an error message but a design change.
- **Concise**: we help our users focus on solving their problems and deliver value, not on dumping tons of data on them.
- **Thorough**: we do not make guesses on the context and knowledge of our users. We provide as much context as possible.
- **Actionable**: we explain how to solve the problem as much as we can, and give links to additional documentation whenever possible.

### Example

- **Terrible**: `unexpected value`.
- **Bad**: `argument must be a string, an int, or a period`.
- **Good**: `Variable {0} has already been set for all months contained in period {1}, and value {2} provided for {1} doesn't match the total ({3}).`
- **Great**: `Inconsistent input: variable {0} has already been set for all months contained in period {1}, and value {2} provided for {1} doesn't match the total ({3}). This error may also be thrown if you try to call set_input twice for the same variable and period. See more at <https://openfisca.org/doc/key-concepts/periodsinstants.html>.`

[More information](https://blogs.mulesoft.com/dev/api-dev/api-best-practices-response-handling/).

## Documentation

OpenFisca does not yet follow a common convention for docstrings, so you'll find [ReStructuredText](https://www.sphinx-doc.org/en/master/usage/restructuredtext/domains.html), [Google](http://google.github.io/styleguide/pyguide.html#Comments), and [NumPy](https://github.com/numpy/numpy/blob/master/doc/HOWTO_DOCUMENT.rst.txt) style docstrings.

Whatever the style you choose, contributors and reusers alike will be more than thankful for the effort you put in documenting your contributions. Here are some general good practices you can follow:

1. TL;DR: Document your intent :smiley:

2. When adding a new module with several classes and functions, please structure it in different files, create an `__init__.py` file and document it as follows:

```py
"""Short summary of your module.

A longer description of what are your module's motivation, domain, and use 
cases. For example, if you decide to create a caching system for OpenFisca, 
consisting on different caching mechanisms, you could say that large operations 
are expensive for some users, that different caching mechanisms exist, and that 
this module implements some of them.

You can then give examples on how to use your module:

    .. code-block:: python

        this = cache(result)
        that = this.flush()

Better you can write `doctests` that will be run with the test suite:

    >>> from . import Cache
    >>> cache = Cache("VFS")
    >>> cache.add("ratio", .45)
    >>> cache.get("ratio")
    .45

"""

from .cache import Cache
from .strategies import Memory, Disk

__all__ = ["Cache", "Memory", "Disk"]
```

3. When adding a new class, you can either document the class itself, the `__init__` method, or both:

```py
class Cache:
    """Implements a new caching system.

    Same as before, you could say this is good because virtuals systems are 
    great but the need a wrapper to make them work with OpenFisca.

    Document the class attributes —different from the initialisation arguments:
        type (str): Type of cache.
        path (str): An so on…

    Document the class arguments, here or in the `__init__` method:
        type: For example if you need a ``type`` to create the :class:`.Cache`.

    Please note that if you're using Python type annotations, you don't need to
    specify types in the documentation, they will be parsed and verified
    automatically.

    """

    def __init__(self, type: str) -> None:
        pass

```

4. Finally, when adding methods to your class, or helper functions to your module, it is very important to document their contracts:

```py
def get(self, key: str) -> Any:
    """Again, summary description.

    The long description is optional, as long as the code is easy to 
    understand. However, there are four key elements to help others understand
    what the code does:

        * What it takes as arguments
        * What it returns
        * What happens if things fail
        * Valid examples that can be run!

    For example if we were following the Google style, it would look like this:

    Args:
        key: The ``key`` to retrieve from the :obj:`.Cache`.

    Returns:
        Whatever we stored, if we stored it (see, no need to specify the type)

    Raises:
        :exc:`KeyNotFoundError`: When the ``key`` wasn't found.

    Examples:
        >>> cache = Cache()
        >>> cache.set("key", "value")
        >>> cache.get("key")
        "value"

    Note:
        Your examples should be simple and illustrative. For more complex
        scenarios write a regular test.

    Todo:
        * Accept :obj:`int` as ``key``.
        * Return None when key is not found.

    .. versionadded:: 1.2.3
        This will help people to undestand the code evolution.

    .. deprecated:: 2.3.4
        This, to have time to adapt their own codebases before the code is
        removed forever.

    .. seealso::
        Finally, you can help users by referencing useful documentation of
        other code, like :mod:`numpy.linalg`, or even links, like the official
        OpenFisca `documentation`_.

    .. _documentation: https://openfisca.org/doc/

    """

    pass

```
