from collections import OrderedDict

from openfisca_core.parameters import helpers, ParameterNode


class ParameterScaleBracket(ParameterNode):
    """
    A parameter scale bracket.
    """

    _allowed_keys = set(['amount', 'threshold', 'rate', 'average_rate', 'base'])

    def to_yaml(self):
        """Return a representation of the Bracket ready to be serialized to YAML."""
        yaml_dict = {}
        for key in self._allowed_keys:
            value = getattr(self, key, None)
            if value is not None:
                yaml_dict[key] = value.values_as_yaml()
        return OrderedDict(sorted(helpers._without_none_values(yaml_dict).items()))
