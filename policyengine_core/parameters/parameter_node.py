import copy
import os
import typing
from typing import Iterable, List, Type, Union

from policyengine_core import commons, parameters, tools
from policyengine_core.data_structures import Reference
from policyengine_core.periods.instant_ import Instant

from .at_instant_like import AtInstantLike
from .parameter import Parameter
from .parameter_node_at_instant import ParameterNodeAtInstant
from .config import COMMON_KEYS, FILE_EXTENSIONS
from .helpers import (
    load_parameter_file,
    _compose_name,
    _validate_parameter,
    _parse_child,
    _load_yaml_file,
)

EXCLUDED_PARAMETER_CHILD_NAMES = ["reference", "__pycache__"]


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
        self.metadata: dict = {}

        if directory_path:
            self.file_path = directory_path
            for child_name in os.listdir(directory_path):
                child_path = os.path.join(directory_path, child_name)
                if os.path.isfile(child_path):
                    child_name, ext = os.path.splitext(child_name)

                    # We ignore non-YAML files
                    if ext not in FILE_EXTENSIONS:
                        continue

                    if child_name == "index":
                        data = _load_yaml_file(child_path) or {}
                        _validate_parameter(
                            self, data, allowed_keys=COMMON_KEYS
                        )
                        self.description = data.get("description")
                        self.documentation = data.get("documentation")
                        self.metadata.update(data.get("metadata", {}))
                    elif child_name not in EXCLUDED_PARAMETER_CHILD_NAMES:
                        child_name_expanded = _compose_name(name, child_name)
                        child = load_parameter_file(
                            child_path, child_name_expanded
                        )
                        self.add_child(child_name, child)

                elif os.path.isdir(child_path):
                    child_name = os.path.basename(child_path)
                    child_name_expanded = _compose_name(name, child_name)
                    child = ParameterNode(
                        child_name_expanded, directory_path=child_path
                    )
                    self.add_child(child_name, child)

        else:
            self.file_path = file_path
            _validate_parameter(
                self, data, data_type=dict, allowed_keys=self._allowed_keys
            )
            self.description = data.get("description")
            self.documentation = data.get("documentation")
            self.metadata.update(data.get("metadata", {}))
            for child_name, child in data.items():
                if (
                    child_name in COMMON_KEYS
                    or child_name in EXCLUDED_PARAMETER_CHILD_NAMES
                ):
                    continue  # do not treat reserved keys as subparameters.

                child_name = str(child_name)
                child_name_expanded = _compose_name(name, child_name)
                child = _parse_child(child_name_expanded, child, file_path)
                self.add_child(child_name, child)

    def merge(self, other: "ParameterNode") -> None:
        """
        Merges another ParameterNode into the current node.

        In case of child name conflict, the other node child will replace the current node child.
        """
        for child_name, child in other.children.items():
            self.add_child(child_name, child)

    def add_child(self, name: str, child: Union["ParameterNode", Parameter]):
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

    def get_descendants(self) -> Iterable[Union["ParameterNode", Parameter]]:
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
