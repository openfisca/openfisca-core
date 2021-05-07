from collections import abc

from openfisca_core.parameters import ParameterNode


class ParameterScaleBracket(ParameterNode, abc.MutableMapping):
    """
    A parameter scale bracket.
    """

    _allowed_keys = set([
        "amount",
        "average_rate",
        "base",
        "children",
        "description",
        "documentation",
        "file_path",
        "metadata",
        "name",
        "rate",
        "threshold",
        ])

    def __setitem__(self, key, value):
        self.__dict__[key] = value

    def __getitem__(self, key):
        return self.__dict__[key]

    def __delitem__(self, key):
        del self.__dict__[key]

    def __iter__(self):
        return iter(self.__dict__)

    def __len__(self):
        return len(self.__dict__)
