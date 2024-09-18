import datetime

from openfisca_core import indexed_enums as enums
from openfisca_core import types as t

VALUE_TYPES = {
    bool: {
        "dtype": t.ArrayBool,
        "default": False,
        "json_type": "boolean",
        "formatted_value_type": "Boolean",
        "is_period_size_independent": True,
    },
    int: {
        "dtype": t.ArrayInt,
        "default": 0,
        "json_type": "integer",
        "formatted_value_type": "Int",
        "is_period_size_independent": False,
    },
    float: {
        "dtype": t.ArrayFloat,
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
    enums.Enum: {
        "dtype": t.ArrayEnum,
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
