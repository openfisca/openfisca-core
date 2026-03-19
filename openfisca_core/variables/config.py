import datetime

import numpy

from openfisca_core import indexed_enums
from openfisca_core.indexed_enums import Enum

VALUE_TYPES = {
    bool: {
        "dtype": numpy.bool_,
        "default": False,
        "json_type": "boolean",
        "formatted_value_type": "Boolean",
        "is_period_size_independent": True,
    },
    int: {
        "dtype": numpy.int32,
        "default": 0,
        "json_type": "integer",
        "formatted_value_type": "Int",
        "is_period_size_independent": False,
    },
    float: {
        "dtype": numpy.float32,
        "default": 0,
        "json_type": "number",
        "formatted_value_type": "Float",
        "is_period_size_independent": False,
    },
    str: {
        "dtype": object,
        "default": "",
        "json_type": "string",
        "formatted_value_type": "String",
        "is_period_size_independent": True,
    },
    Enum: {
        "dtype": indexed_enums.ENUM_ARRAY_DTYPE,
        "json_type": "string",
        "formatted_value_type": "String",
        "is_period_size_independent": True,
    },
    datetime.date: {
        "dtype": "datetime64[D]",
        "default": datetime.date.fromtimestamp(0),  # 0 == 1970-01-01
        "json_type": "string",
        "formatted_value_type": "Date",
        "is_period_size_independent": True,
    },
}


FORMULA_NAME_PREFIX = "formula"
