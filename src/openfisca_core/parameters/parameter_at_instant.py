import copy
import typing

from openfisca_core import commons
from openfisca_core.errors import ParameterParsingError
from openfisca_core.parameters import config, helpers


class ParameterAtInstant:
    """
    A value of a parameter at a given instant.
    """

    # 'unit' and 'reference' are only listed here for backward compatibility
    _allowed_keys = set(['value', 'metadata', 'unit', 'reference'])

    def __init__(self, name, instant_str, data = None, file_path = None, metadata = None):
        """
        :param string name: name of the parameter, e.g. "taxes.some_tax.some_param"
        :param string instant_str: Date of the value in the format `YYYY-MM-DD`.
        :param dict data: Data, usually loaded from a YAML file.
        """
        self.name: str = name
        self.instant_str: str = instant_str
        self.file_path: str = file_path
        self.metadata: typing.Dict = {}

        # Accept { 2015-01-01: 4000 }
        if not isinstance(data, dict) and isinstance(data, config.ALLOWED_PARAM_TYPES):
            self.value = data
            return

        self.validate(data)
        self.value: float = data['value']

        if metadata is not None:
            self.metadata.update(metadata)  # Inherit metadata from Parameter
        helpers._set_backward_compatibility_metadata(self, data)
        self.metadata.update(data.get('metadata', {}))

    def validate(self, data):
        helpers._validate_parameter(self, data, data_type = dict, allowed_keys = self._allowed_keys)
        try:
            value = data['value']
        except KeyError:
            raise ParameterParsingError(
                "Missing 'value' property for {}".format(self.name),
                self.file_path
                )
        if not isinstance(value, config.ALLOWED_PARAM_TYPES):
            raise ParameterParsingError(
                "Value in {} has type {}, which is not one of the allowed types ({}): {}".format(self.name, type(value), config.ALLOWED_PARAM_TYPES, value),
                self.file_path
                )

    def __eq__(self, other):
        return (self.name == other.name) and (self.instant_str == other.instant_str) and (self.value == other.value)

    def __repr__(self):
        return "ParameterAtInstant({})".format({self.instant_str: self.value})

    def clone(self):
        clone = commons.empty_clone(self)
        clone.__dict__ = self.__dict__.copy()
        clone.metadata = copy.deepcopy(self.metadata)
        return clone
