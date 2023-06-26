import copy

from openfisca_core import commons
from openfisca_core.errors import ParameterParsingError
from openfisca_core.parameters import config, helpers


class ParameterAtInstant:
    """A value of a parameter at a given instant."""

    # 'unit' and 'reference' are only listed here for backward compatibility
    _allowed_keys = {"value", "metadata", "unit", "reference"}

    def __init__(
        self, name, instant_str, data=None, file_path=None, metadata=None
    ) -> None:
        """:param str name: name of the parameter, e.g. "taxes.some_tax.some_param"
        :param str instant_str: Date of the value in the format `YYYY-MM-DD`.
        :param dict data: Data, usually loaded from a YAML file.
        """
        self.name: str = name
        self.instant_str: str = instant_str
        self.file_path: str = file_path
        self.metadata: dict = {}

        # Accept { 2015-01-01: 4000 }
        if not isinstance(data, dict) and isinstance(data, config.ALLOWED_PARAM_TYPES):
            self.value = data
            return

        self.validate(data)
        self.value: float = data["value"]

        if metadata is not None:
            self.metadata.update(metadata)  # Inherit metadata from Parameter
        helpers._set_backward_compatibility_metadata(self, data)
        self.metadata.update(data.get("metadata", {}))

    def validate(self, data) -> None:
        helpers._validate_parameter(
            self,
            data,
            data_type=dict,
            allowed_keys=self._allowed_keys,
        )
        try:
            value = data["value"]
        except KeyError:
            msg = f"Missing 'value' property for {self.name}"
            raise ParameterParsingError(
                msg,
                self.file_path,
            )
        if not isinstance(value, config.ALLOWED_PARAM_TYPES):
            msg = f"Value in {self.name} has type {type(value)}, which is not one of the allowed types ({config.ALLOWED_PARAM_TYPES}): {value}"
            raise ParameterParsingError(
                msg,
                self.file_path,
            )

    def __eq__(self, other):
        return (
            (self.name == other.name)
            and (self.instant_str == other.instant_str)
            and (self.value == other.value)
        )

    def __repr__(self) -> str:
        return "ParameterAtInstant({self.instant_str: self.value})"

    def clone(self):
        clone = commons.empty_clone(self)
        clone.__dict__ = self.__dict__.copy()
        clone.metadata = copy.deepcopy(self.metadata)
        return clone
