from __future__ import annotations

from typing import NoReturn

import datetime
import re
import textwrap

import numpy
import sortedcontainers

from openfisca_core import commons, periods, types as t
from openfisca_core.entities import Entity, GroupEntity
from openfisca_core.indexed_enums import Enum, EnumArray
from openfisca_core.periods import DateUnit, Period

from . import config, helpers


class Variable:
    """A `variable <https://openfisca.org/doc/key-concepts/variables.html>`_ of the legislation.

    Main attributes:

       .. attribute:: name

           Name of the variable

       .. attribute:: value_type

           The value type of the variable. Possible value types in OpenFisca are ``int`` ``float`` ``bool`` ``str`` ``date`` and ``Enum``.

       .. attribute:: entity

           `Entity <https://openfisca.org/doc/key-concepts/person,_entities,_role.html>`_ the variable is defined for. For instance : ``Person``, ``Household``.

       .. attribute:: definition_period

           `Period <https://openfisca.org/doc/coding-the-legislation/35_periods.html>`_ the variable is defined for. Possible value: ``DateUnit.DAY``, ``DateUnit.MONTH``, ``DateUnit.YEAR``, ``DateUnit.ETERNITY``.

       .. attribute:: formulas

           Formulas used to calculate the variable

       .. attribute:: label

           Description of the variable

       .. attribute:: reference

           Legislative reference describing the variable.

       .. attribute:: default_value

           `Default value <https://openfisca.org/doc/key-concepts/variables.html#default-values>`_ of the variable.

    Secondary attributes:

       .. attribute:: baseline_variable

           If the variable has been introduced in a `reform <https://openfisca.org/doc/key-concepts/reforms.html>`_ to replace another variable, baseline_variable is the replaced variable.

       .. attribute:: dtype

           Numpy `dtype <https://docs.scipy.org/doc/numpy-1.13.0/reference/generated/numpy.dtype.html>`_ used under the hood for the variable.

       .. attribute:: end

           `Date <https://openfisca.org/doc/coding-the-legislation/40_legislation_evolutions.html#variable-end>`_  when the variable disappears from the legislation.

       .. attribute:: is_neutralized

           True if the variable is neutralized. Neutralized variables never use their formula, and only return their default values when calculated.

       .. attribute:: json_type

           JSON type corresponding to the variable.

       .. attribute:: max_length

           If the value type of the variable is ``str``, max length of the string allowed. ``None`` if there is no limit.

       .. attribute:: possible_values

           If the value type of the variable is ``Enum``, contains the values the variable can take.

       .. attribute:: set_input

           Function used to automatically process variable inputs defined for periods not matching the definition_period of the variable. See more on the `documentation <https://openfisca.org/doc/coding-the-legislation/35_periods.html#set-input-automatically-process-variable-inputs-defined-for-periods-not-matching-the-definition-period>`_. Possible values are ``set_input_dispatch_by_period``, ``set_input_divide_by_period``, or nothing.

       .. attribute:: unit

           Free text field describing the unit of the variable. Only used as metadata.

       .. attribute:: documentation

           Free multilines text field describing the variable context and usage.
    """

    __name__: str

    def __init__(self, baseline_variable=None) -> None:
        self.name = self.__class__.__name__
        attr = {
            name: value
            for name, value in self.__class__.__dict__.items()
            if not name.startswith("__")
        }
        self.baseline_variable = baseline_variable
        self.value_type = self.set(
            attr,
            "value_type",
            required=True,
            allowed_values=config.VALUE_TYPES.keys(),
        )
        self.dtype = config.VALUE_TYPES[self.value_type]["dtype"]
        self.json_type = config.VALUE_TYPES[self.value_type]["json_type"]
        if self.value_type == Enum:
            self.possible_values = self.set(
                attr,
                "possible_values",
                required=True,
                setter=self.set_possible_values,
            )
        if self.value_type == str:
            self.max_length = self.set(attr, "max_length", allowed_type=int)
            if self.max_length:
                self.dtype = f"|S{self.max_length}"
        if self.value_type == Enum:
            self.default_value = self.set(
                attr,
                "default_value",
                allowed_type=self.possible_values,
                required=True,
            )
        else:
            self.default_value = self.set(
                attr,
                "default_value",
                allowed_type=self.value_type,
                default=config.VALUE_TYPES[self.value_type].get("default"),
            )
        self.entity = self.set(attr, "entity", required=True, setter=self.set_entity)
        self.definition_period = self.set(
            attr,
            "definition_period",
            required=True,
            allowed_values=DateUnit,
        )
        self.label = self.set(attr, "label", allowed_type=str, setter=self.set_label)
        self.end = self.set(attr, "end", allowed_type=str, setter=self.set_end)
        self.reference = self.set(attr, "reference", setter=self.set_reference)
        self.cerfa_field = self.set(attr, "cerfa_field", allowed_type=(str, dict))
        self.unit = self.set(attr, "unit", allowed_type=str)
        self.documentation = self.set(
            attr,
            "documentation",
            allowed_type=str,
            setter=self.set_documentation,
        )
        self.set_input = self.set_set_input(attr.pop("set_input", None))
        self.calculate_output = self.set_calculate_output(
            attr.pop("calculate_output", None),
        )
        self.is_period_size_independent = self.set(
            attr,
            "is_period_size_independent",
            allowed_type=bool,
            default=config.VALUE_TYPES[self.value_type]["is_period_size_independent"],
        )

        self.introspection_data = self.set(
            attr,
            "introspection_data",
        )

        formulas_attr, unexpected_attrs = helpers._partition(
            attr,
            lambda name, value: name.startswith(config.FORMULA_NAME_PREFIX),
        )
        self.formulas = self.set_formulas(formulas_attr)

        if unexpected_attrs:
            msg = 'Unexpected attributes in definition of variable "{}": {!r}'.format(
                self.name,
                ", ".join(sorted(unexpected_attrs.keys())),
            )
            raise ValueError(
                msg,
            )

        self.is_neutralized = False

    # ----- Setters used to build the variable ----- #

    def set(
        self,
        attributes,
        attribute_name,
        required=False,
        allowed_values=None,
        allowed_type=None,
        setter=None,
        default=None,
    ):
        value = attributes.pop(attribute_name, None)
        if value is None and self.baseline_variable:
            return getattr(self.baseline_variable, attribute_name)
        if required and value is None:
            msg = f"Missing attribute '{attribute_name}' in definition of variable '{self.name}'."
            raise ValueError(
                msg,
            )
        if allowed_values is not None and value not in allowed_values:
            msg = f"Invalid value '{value}' for attribute '{attribute_name}' in variable '{self.name}'. Allowed values are '{allowed_values}'."
            raise ValueError(
                msg,
            )
        if (
            allowed_type is not None
            and value is not None
            and not isinstance(value, allowed_type)
        ):
            if allowed_type == float and isinstance(value, int):
                value = float(value)
            else:
                msg = f"Invalid value '{value}' for attribute '{attribute_name}' in variable '{self.name}'. Must be of type '{allowed_type}'."
                raise ValueError(
                    msg,
                )
        if setter is not None:
            value = setter(value)
        if value is None and default is not None:
            return default
        return value

    def set_entity(self, entity):
        if not isinstance(entity, (Entity, GroupEntity)):
            msg = (
                f"Invalid value '{entity}' for attribute 'entity' in variable "
                f"'{self.name}'. Must be an instance of Entity or GroupEntity."
            )
            raise ValueError(
                msg,
            )
        return entity

    def set_possible_values(self, possible_values):
        if not issubclass(possible_values, Enum):
            msg = f"Invalid value '{possible_values}' for attribute 'possible_values' in variable '{self.name}'. Must be a subclass of {Enum}."
            raise ValueError(
                msg,
            )
        return possible_values

    def set_label(self, label):
        if label:
            return label
        return None

    def set_end(self, end):
        if end:
            try:
                return datetime.datetime.strptime(end, "%Y-%m-%d").date()
            except ValueError:
                msg = f"Incorrect 'end' attribute format in '{self.name}'. 'YYYY-MM-DD' expected where YYYY, MM and DD are year, month and day. Found: {end}"
                raise ValueError(
                    msg,
                )
        return None

    def set_reference(self, reference):
        if reference:
            if isinstance(reference, str):
                reference = [reference]
            elif isinstance(reference, list):
                pass
            elif isinstance(reference, tuple):
                reference = list(reference)
            else:
                msg = f"The reference of the variable {self.name} is a {type(reference)} instead of a String or a List of Strings."
                raise TypeError(
                    msg,
                )

            for element in reference:
                if not isinstance(element, str):
                    msg = f"The reference of the variable {self.name} is a {type(reference)} instead of a String or a List of Strings."
                    raise TypeError(
                        msg,
                    )

        return reference

    def set_documentation(self, documentation):
        if documentation:
            return textwrap.dedent(documentation)
        return None

    def set_set_input(self, set_input):
        if not set_input and self.baseline_variable:
            return self.baseline_variable.set_input
        return set_input

    def set_calculate_output(self, calculate_output):
        if not calculate_output and self.baseline_variable:
            return self.baseline_variable.calculate_output
        return calculate_output

    def set_formulas(self, formulas_attr):
        formulas = sortedcontainers.sorteddict.SortedDict()
        for formula_name, formula in formulas_attr.items():
            starting_date = self.parse_formula_name(formula_name)

            if self.end is not None and starting_date > self.end:
                msg = f'You declared that "{self.name}" ends on "{self.end}", but you wrote a formula to calculate it from "{starting_date}" ({formula_name}). The "end" attribute of a variable must be posterior to the start dates of all its formulas.'
                raise ValueError(
                    msg,
                )

            formulas[str(starting_date)] = formula

        # If the variable is reforming a baseline variable, keep the formulas from the latter when they are not overridden by new formulas.
        if self.baseline_variable is not None:
            first_reform_formula_date = formulas.peekitem(0)[0] if formulas else None
            formulas.update(
                {
                    baseline_start_date: baseline_formula
                    for baseline_start_date, baseline_formula in self.baseline_variable.formulas.items()
                    if first_reform_formula_date is None
                    or baseline_start_date < first_reform_formula_date
                },
            )

        return formulas

    def parse_formula_name(self, attribute_name):
        """Returns the starting date of a formula based on its name.

        Valid dated name formats are : 'formula', 'formula_YYYY', 'formula_YYYY_MM' and 'formula_YYYY_MM_DD' where YYYY, MM and DD are a year, month and day.

        By convention, the starting date of:
            - `formula` is `0001-01-01` (minimal date in Python)
            - `formula_YYYY` is `YYYY-01-01`
            - `formula_YYYY_MM` is `YYYY-MM-01`
        """

        def raise_error() -> NoReturn:
            msg = f'Unrecognized formula name in variable "{self.name}". Expecting "formula_YYYY" or "formula_YYYY_MM" or "formula_YYYY_MM_DD where YYYY, MM and DD are year, month and day. Found: "{attribute_name}".'
            raise ValueError(
                msg,
            )

        if attribute_name == config.FORMULA_NAME_PREFIX:
            return datetime.date.min

        FORMULA_REGEX = r"formula_(\d{4})(?:_(\d{2}))?(?:_(\d{2}))?$"  # YYYY or YYYY_MM or YYYY_MM_DD

        match = re.match(FORMULA_REGEX, attribute_name)
        if not match:
            raise_error()
        date_str = "-".join(
            [match.group(1), match.group(2) or "01", match.group(3) or "01"],
        )

        try:
            return datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:  # formula_2005_99_99 for instance
            raise_error()

    # ----- Methods ----- #

    def is_input_variable(self):
        """Returns True if the variable is an input variable."""
        return len(self.formulas) == 0

    @classmethod
    def get_introspection_data(cls):
        try:
            return cls.introspection_data
        except AttributeError:
            return "", None, 0

    def get_formula(
        self,
        period: None | t.Instant | t.Period | str | int = None,
    ) -> None | t.Formula:
        """Returns the formula to compute the variable at the given period.

        If no period is given and the variable has several formulas, the method
        returns the oldest formula.

        Args:
            period: The period to get the formula.

        Returns:
            Formula used to compute the variable.

        """
        instant: None | t.Instant

        if not self.formulas:
            return None

        if period is None:
            return self.formulas.peekitem(
                index=0,
            )[
                1
            ]  # peekitem gets the 1st key-value tuple (the oldest start_date and formula). Return the formula.

        if isinstance(period, Period):
            instant = period.start
        else:
            try:
                instant = periods.period(period).start
            except ValueError:
                instant = periods.instant(period)

        if instant is None:
            return None

        if self.end and instant.date > self.end:
            return None

        instant_str = str(instant)

        for start_date in reversed(self.formulas):
            if start_date <= instant_str:
                return self.formulas[start_date]

        return None

    def clone(self):
        return self.__class__()

    def check_set_value(self, value):
        if self.value_type == Enum and isinstance(value, str):
            try:
                value = self.possible_values[value].index
            except KeyError:
                possible_values = [item.name for item in self.possible_values]
                msg = "'{}' is not a known value for '{}'. Possible values are ['{}'].".format(
                    value,
                    self.name,
                    "', '".join(possible_values),
                )
                raise ValueError(
                    msg,
                )
        if self.value_type in (float, int) and isinstance(value, str):
            try:
                value = commons.eval_expression(value)
            except SyntaxError:
                msg = f"I couldn't understand '{value}' as a value for '{self.name}'"
                raise ValueError(
                    msg,
                )

        try:
            value = numpy.array([value], dtype=self.dtype)[0]
        except (TypeError, ValueError):
            if self.value_type == datetime.date:
                error_message = f"Can't deal with date: '{value}'."
            else:
                error_message = f"Can't deal with value: expected type {self.json_type}, received '{value}'."
            raise ValueError(error_message)
        except OverflowError:
            error_message = f"Can't deal with value: '{value}', it's too large for type '{self.json_type}'."
            raise ValueError(error_message)

        return value

    def default_array(self, array_size):
        array = numpy.empty(array_size, dtype=self.dtype)
        if self.value_type == Enum:
            array.fill(self.default_value.index)
            return EnumArray(array, self.possible_values)
        array.fill(self.default_value)
        return array
