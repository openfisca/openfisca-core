from __future__ import annotations

import copy
import os
import typing
from typing import Iterable, List, Type, Union
from policyengine_core import commons, parameters, tools
from policyengine_core.periods.instant_ import Instant
from policyengine_core.data_structures import Reference
from . import config, helpers, AtInstantLike, Parameter, ParameterNodeAtInstant

class ParameterNodeMetadata:
    name: str
    """The name of the parameter. Should be snake-case, and Python-safe."""
    label: str
    """The label of the parameter. Should be human-readable."""
    description: str
    """A description of the parameter and its legal meaning."""
    documentation: str
    """A description of any implementation details (e.g. details about how it is modelled within the simulation)."""
    unit: str
    """The unit of the parameter, eg `currency-GBP`."""
    breakdown: List[str]
    """The set of child names under this parameter node. These children will be automatically created if they do not exist."""
    references: List[Reference]
    """A list of references to legislation, policy documents, or other sources."""

    def __init__(self, name: str, data: dict, reference_types: List[Type[Reference]] = None):
        self.name = name
        self.label = data.get("label", name)
        self.description = data.get("description")
        self.documentation = data.get("documentation")
        self.unit = data.get("unit")
        self.breakdown = data.get("breakdown")
        reference_types = {reference.type: reference for reference in reference_types} if reference_types else {}
        self.references = [
            reference_types.get(data.get("type"), Reference)(**ref) for ref in data.get("references", [])
        ]
    
    def __getitem__(self, key):
        return getattr(self, key)
    
    def get(self, key, default = None):
        return getattr(self, key, default)
    
    def __setitem__(self, key, value):
        setattr(self, key, value)


class ParameterNode(AtInstantLike):
    """
    A node in the legislation `parameter tree <https://openfisca.org/doc/coding-the-legislation/legislation_parameters.html>`_.
    """

    _allowed_keys: typing.Optional[
        typing.Iterable[str]
    ] = None  # By default, no restriction on the keys

    parent: "ParameterNode" = None
    """The parent of the node, or None if the node is the root of the tree."""

    def __init__(
        self,
        name: str = "",
        directory_path: str = None,
        data: dict = None,
        file_path: str = None,
        reference_types: List[Type[Reference]] = None,
    ):
        """
        Instantiate a ParameterNode either from a dict, (using `data`), or from a directory containing YAML files (using `directory_path`).

        :param str name: Name of the node, eg "taxes.some_tax".
        :param str directory_path: Directory containing YAML files describing the node.
        :param dict data: Object representing the parameter node. It usually has been extracted from a YAML file.
        :param str file_path: YAML file from which the `data` has been extracted from.


        Instantiate a ParameterNode from a dict:

        >>> node = ParameterNode('basic_income', data = {
            'amount': {
              'values': {
                "2015-01-01": {'value': 550},
                "2016-01-01": {'value': 600}
                }
              },
            'min_age': {
              'values': {
                "2015-01-01": {'value': 25},
                "2016-01-01": {'value': 18}
                }
              },
            })

        Instantiate a ParameterNode from a directory containing YAML parameter files:

        >>> node = ParameterNode('benefits', directory_path = '/path/to/country_package/parameters/benefits')
        """
        self.name: str = name
        self.children: typing.Dict[
            str,
            typing.Union[ParameterNode, Parameter, parameters.ParameterScale],
        ] = {}
        self.description: str = None
        self.documentation: str = None
        self.file_path: str = None
        self.metadata: ParameterNodeMetadata = {}
        if reference_types is None:
            reference_types = []

        if directory_path:
            self.file_path = directory_path
            for child_name in os.listdir(directory_path):
                child_path = os.path.join(directory_path, child_name)
                if os.path.isfile(child_path):
                    child_name, ext = os.path.splitext(child_name)

                    # We ignore non-YAML files
                    if ext not in config.FILE_EXTENSIONS:
                        continue

                    if child_name == "index":
                        data = helpers._load_yaml_file(child_path) or {}
                        helpers._validate_parameter(
                            self, data, allowed_keys=config.COMMON_KEYS
                        )
                        self.description = data.get("description")
                        self.documentation = data.get("documentation")
                        self.metadata.update(data.get("metadata", {}))
                    else:
                        child_name_expanded = helpers._compose_name(
                            name, child_name
                        )
                        child = helpers.load_parameter_file(
                            child_path, child_name_expanded
                        )
                        self.add_child(child_name, child)

                elif os.path.isdir(child_path):
                    child_name = os.path.basename(child_path)
                    child_name_expanded = helpers._compose_name(
                        name, child_name
                    )
                    child = ParameterNode(
                        child_name_expanded, directory_path=child_path
                    )
                    self.add_child(child_name, child)

        else:
            self.file_path = file_path
            helpers._validate_parameter(
                self, data, data_type=dict, allowed_keys=self._allowed_keys
            )
            self.description = data.get("description")
            self.documentation = data.get("documentation")
            self.metadata.update(data.get("metadata", {}))
            for child_name, child in data.items():
                if child_name in config.COMMON_KEYS:
                    continue  # do not treat reserved keys as subparameters.

                child_name = str(child_name)
                child_name_expanded = helpers._compose_name(name, child_name)
                child = helpers._parse_child(
                    child_name_expanded, child, file_path
                )
                self.add_child(child_name, child)
        self.metadata = ParameterNodeMetadata(self.name, self.metadata)

    def merge(self, other: "ParameterNode") -> None:
        """
        Merges another ParameterNode into the current node.

        In case of child name conflict, the other node child will replace the current node child.
        """
        for child_name, child in other.children.items():
            self.add_child(child_name, child)

    def add_child(self, name: str, child: Union[ParameterNode, Parameter]):
        """
        Add a new child to the node.

        :param name: Name of the child that must be used to access that child. Should not contain anything that could interfere with the operator `.` (dot).
        :param child: The new child, an instance of :class:`.ParameterScale` or :class:`.Parameter` or :class:`.ParameterNode`.
        """
        if name in self.children:
            raise ValueError(
                "{} has already a child named {}".format(self.name, name)
            )
        if not (
            isinstance(child, ParameterNode)
            or isinstance(child, Parameter)
            or isinstance(child, parameters.ParameterScale)
        ):
            raise TypeError(
                "child must be of type ParameterNode, Parameter, or Scale. Instead got {}".format(
                    type(child)
                )
            )
        self.children[name] = child
        setattr(self, name, child)
        child.parent = self

    def __repr__(self) -> str:
        result = os.linesep.join(
            [
                os.linesep.join(["{}:", "{}"]).format(
                    name, tools.indent(repr(value))
                )
                for name, value in sorted(self.children.items())
            ]
        )
        return result

    def get_descendants(self) -> Iterable[Union[ParameterNode, Parameter]]:
        """
        Return a generator containing all the parameters and nodes recursively contained in this `ParameterNode`
        """
        for child in self.children.values():
            yield child
            yield from child.get_descendants()

    def clone(self) -> "ParameterNode":
        clone = commons.empty_clone(self)
        clone.__dict__ = self.__dict__.copy()

        clone.metadata = copy.deepcopy(self.metadata)
        clone.children = {
            key: child.clone() for key, child in self.children.items()
        }
        for child_key, child in clone.children.items():
            setattr(clone, child_key, child)

        return clone

    def _get_at_instant(self, instant: Instant) -> ParameterNodeAtInstant:
        return ParameterNodeAtInstant(self.name, self, instant)
    
    def attach_to_parent(self, parent: "ParameterNode"):
        self.parent = parent
