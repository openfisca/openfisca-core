Thank you for wanting to contribute to OpenFisca! :smiley:

TL;DR: [GitHub Flow](https://guides.github.com/introduction/flow/), [SemVer](http://semver.org/), sweat on naming and messages.


## Common guidelines for all OpenFisca modules

[Common contributor guidelines](https://doc.openfisca.fr/contribute/guidelines.html).


## Pull requests

We follow the [GitHub Flow](https://guides.github.com/introduction/flow/): all code contributions are submitted via a pull request towards the `master` branch.

Opening a Pull Request means you want that code to be merged. If you want to only discuss it, send a link to your branch along with your questions through whichever communication channel you prefer.

If the Pull Request depends on another opened Pull Request on another repository (like OpenFisca-Core/OpenFisca-France), the requirements should be updated in the dependent project via its `setup.py`.

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

> **Terrible**: `unexpected value`.
> **Bad**: `argument must be a string, an int, or a period`.
> **Good**: `Variable {0} has already been set for all months contained in period {1}, and value {2} provided for {1} doesn't match the total ({3}).`
> **Great**: `Inconsistent input: variable {0} has already been set for all months contained in period {1}, and value {2} provided for {1} doesn't match the total ({3}). This error may also be thrown if you try to call set_input twice for the same variable and period. See more at <https://doc.openfisca.fr/periodsinstants.html>.`

[More information](https://blogs.mulesoft.com/dev/api-dev/api-best-practices-response-handling/).
