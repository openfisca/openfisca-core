import datetime
import inspect
import re
import textwrap
from typing import Callable, List, Type
import sortedcontainers

import numpy

from policyengine_core import periods, tools
from policyengine_core.entities import Entity
from policyengine_core.enums import Enum, EnumArray
from policyengine_core.periods import Period

from . import config, helpers


class QuantityType:
    STOCK = "stock"
    FLOW = "flow"


class Variable:
    """
    A `variable <https://openfisca.org/doc/key-concepts/variables.html>`_ of the legislation.
    """

    name: str
    """Name of the variable"""

    value_type: type
    """The value type of the variable. Possible value types in OpenFisca are ``int`` ``float`` ``bool`` ``str`` ``date`` and ``Enum``."""

    entity: Entity
    """`Entity <https://openfisca.org/doc/key-concepts/person,_entities,_role.html>`_ the variable is defined for. For instance : ``Person``, ``Household``."""

    definition_period: Period
    """`Period <https://openfisca.org/doc/coding-the-legislation/35_periods.html>`_ the variable is defined for. Possible value: ``MONTH``, ``YEAR``, ``ETERNITY``."""

    formulas: List[Callable]
    """Formulas used to calculate the variable"""

    label: str
    """Description of the variable"""

    reference: str
    """Legislative reference describing the variable."""

    default_value: object
    """`Default value <https://openfisca.org/doc/key-concepts/variables.html#default-values>`_ of the variable."""

    baseline_variable: str
    """If the variable has been introduced in a `reform <https://openfisca.org/doc/key-concepts/reforms.html>`_ to replace another variable, baseline_variable is the replaced variable."""

    dtype: numpy.dtype
    """Numpy `dtype <https://docs.scipy.org/doc/numpy-1.13.0/reference/generated/numpy.dtype.html>`_ used under the hood for the variable."""

    end: datetime.date
    """`Date <https://openfisca.org/doc/coding-the-legislation/40_legislation_evolutions.html#variable-end>`_  when the variable disappears from the legislation."""

    is_neutralized: bool
    """True if the variable is neutralized. Neutralized variables never use their formula, and only return their default values when calculated."""

    json_type: str
    """JSON type corresponding to the variable."""

    max_length: int
    """If the value type of the variable is ``str``, max length of the string allowed. ``None`` if there is no limit."""

    possible_values: EnumArray
    """If the value type of the variable is ``Enum``, contains the values the variable can take."""

    set_input: Callable
    """Function used to automatically process variable inputs defined for periods not matching the definition_period of the variable. See more on the `documentation <https://openfisca.org/doc/coding-the-legislation/35_periods.html#set-input-automatically-process-variable-inputs-defined-for-periods-not-matching-the-definition-period>`_. Possible values are ``set_input_dispatch_by_period``, ``set_input_divide_by_period``, or nothing."""

    unit: str
    """Free text field describing the unit of the variable. Only used as metadata."""

    documentation: str
    """Free multilines text field describing the variable context and usage."""

    quantity_type: str
    """Categorical attribute describing whether the variable is a stock or a flow."""

    defined_for: str
    """The name of another variable, nonzero values of which are used to define the set of entities for which this variable is defined."""

    def __init__(self, baseline_variable=None):
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
            self.possible_values: Type[Enum] = self.set(
                attr,
                "possible_values",
                required=True,
                setter=self.set_possible_values,
            )
        if self.value_type == str:
            self.max_length = self.set(attr, "max_length", allowed_type=int)
            if self.max_length:
                self.dtype = "|S{}".format(self.max_length)
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
        self.entity = self.set(
            attr, "entity", required=True, setter=self.set_entity
        )
        self.definition_period = self.set(
            attr,
            "definition_period",
            required=True,
            allowed_values=(
                periods.DAY,
                periods.MONTH,
                periods.YEAR,
                periods.ETERNITY,
            ),
        )
        self.quantity_type = self.set(
            attr,
            "quantity_type",
            required=False,
            allowed_values=(QuantityType.STOCK, QuantityType.FLOW),
            default=QuantityType.FLOW,
        )
        self.label = self.set(
            attr, "label", allowed_type=str, setter=self.set_label
        )
        self.end = self.set(attr, "end", allowed_type=str, setter=self.set_end)
        self.reference = self.set(attr, "reference", setter=self.set_reference)
        self.cerfa_field = self.set(
            attr, "cerfa_field", allowed_type=(str, dict)
        )
        self.unit = self.set(attr, "unit", allowed_type=str)
        self.documentation = self.set(
            attr,
            "documentation",
            allowed_type=str,
            setter=self.set_documentation,
        )
        self.set_input = self.set_set_input(attr.pop("set_input", None))
        self.calculate_output = self.set_calculate_output(
            attr.pop("calculate_output", None)
        )
        self.is_period_size_independent = self.set(
            attr,
            "is_period_size_independent",
            allowed_type=bool,
            default=config.VALUE_TYPES[self.value_type][
                "is_period_size_independent"
            ],
        )

        self.defined_for = self.set_defined_for(attr.pop("defined_for", None))

        formulas_attr, unexpected_attrs = helpers._partition(
            attr,
            lambda name, value: name.startswith(config.FORMULA_NAME_PREFIX),
        )
        self.formulas = self.set_formulas(formulas_attr)

        if unexpected_attrs:
            raise ValueError(
                'Unexpected attributes in definition of variable "{}": {!r}'.format(
                    self.name, ", ".join(sorted(unexpected_attrs.keys()))
                )
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
            raise ValueError(
                "Missing attribute '{}' in definition of variable '{}'.".format(
                    attribute_name, self.name
                )
            )
        if (
            required
            and allowed_values is not None
            and value not in allowed_values
        ):
            raise ValueError(
                "Invalid value '{}' for attribute '{}' in variable '{}'. Allowed values are '{}'.".format(
                    value, attribute_name, self.name, allowed_values
                )
            )
        if (
            allowed_type is not None
            and value is not None
            and not isinstance(value, allowed_type)
        ):
            if allowed_type == float and isinstance(value, int):
                value = float(value)
            else:
                raise ValueError(
                    "Invalid value '{}' for attribute '{}' in variable '{}'. Must be of type '{}'.".format(
                        value, attribute_name, self.name, allowed_type
                    )
                )
        if setter is not None:
            value = setter(value)
        if value is None and default is not None:
            return default
        return value

    def set_entity(self, entity):
        if not isinstance(entity, Entity):
            raise ValueError(
                f"Invalid value '{entity}' for attribute 'entity' in variable '{self.name}'. Must be an instance of Entity."
            )
        return entity

    def set_possible_values(self, possible_values):
        if not issubclass(possible_values, Enum):
            raise ValueError(
                "Invalid value '{}' for attribute 'possible_values' in variable '{}'. Must be a subclass of {}.".format(
                    possible_values, self.name, Enum
                )
            )
        return possible_values

    def set_label(self, label):
        if label:
            return label

    def set_end(self, end):
        if end:
            try:
                return datetime.datetime.strptime(end, "%Y-%m-%d").date()
            except ValueError:
                raise ValueError(
                    "Incorrect 'end' attribute format in '{}'. 'YYYY-MM-DD' expected where YYYY, MM and DD are year, month and day. Found: {}".format(
                        self.name, end
                    )
                )

    def set_reference(self, reference):
        if reference:
            if isinstance(reference, str):
                reference = [reference]
            elif isinstance(reference, list):
                pass
            elif isinstance(reference, tuple):
                reference = list(reference)
            elif isinstance(reference, dict):
                reference = [reference]

        return reference

    def set_documentation(self, documentation):
        if documentation:
            return textwrap.dedent(documentation)

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
                raise ValueError(
                    'You declared that "{}" ends on "{}", but you wrote a formula to calculate it from "{}" ({}). The "end" attribute of a variable must be posterior to the start dates of all its formulas.'.format(
                        self.name, self.end, starting_date, formula_name
                    )
                )

            formulas[str(starting_date)] = formula

        # If the variable is reforming a baseline variable, keep the formulas from the latter when they are not overridden by new formulas.
        if self.baseline_variable is not None:
            first_reform_formula_date = (
                formulas.peekitem(0)[0] if formulas else None
            )
            formulas.update(
                {
                    baseline_start_date: baseline_formula
                    for baseline_start_date, baseline_formula in self.baseline_variable.formulas.items()
                    if first_reform_formula_date is None
                    or baseline_start_date < first_reform_formula_date
                }
            )

        return formulas

    def set_defined_for(self, defined_for):
        if isinstance(defined_for, Enum):
            defined_for = defined_for.value
        return defined_for

    def parse_formula_name(self, attribute_name):
        """
        Returns the starting date of a formula based on its name.

        Valid dated name formats are : 'formula', 'formula_YYYY', 'formula_YYYY_MM' and 'formula_YYYY_MM_DD' where YYYY, MM and DD are a year, month and day.

        By convention, the starting date of:
            - `formula` is `0001-01-01` (minimal date in Python)
            - `formula_YYYY` is `YYYY-01-01`
            - `formula_YYYY_MM` is `YYYY-MM-01`
        """

        def raise_error():
            raise ValueError(
                'Unrecognized formula name in variable "{}". Expecting "formula_YYYY" or "formula_YYYY_MM" or "formula_YYYY_MM_DD where YYYY, MM and DD are year, month and day. Found: "{}".'.format(
                    self.name, attribute_name
                )
            )

        if attribute_name == config.FORMULA_NAME_PREFIX:
            return datetime.date.min

        FORMULA_REGEX = r"formula_(\d{4})(?:_(\d{2}))?(?:_(\d{2}))?$"  # YYYY or YYYY_MM or YYYY_MM_DD

        match = re.match(FORMULA_REGEX, attribute_name)
        if not match:
            raise_error()
        date_str = "-".join(
            [match.group(1), match.group(2) or "01", match.group(3) or "01"]
        )

        try:
            return datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:  # formula_2005_99_99 for instance
            raise_error()

    # ----- Methods ----- #

    def is_input_variable(self):
        """
        Returns True if the variable is an input variable.
        """
        return len(self.formulas) == 0

    @classmethod
    def get_introspection_data(cls, tax_benefit_system):
        """
        Get instrospection data about the code of the variable.

        :returns: (comments, source file path, source code, start line number)
        :rtype: tuple

        """
        comments = inspect.getcomments(cls)

        # Handle dynamically generated variable classes or Jupyter Notebooks, which have no source.
        try:
            absolute_file_path = inspect.getsourcefile(cls)
        except TypeError:
            source_file_path = None
        else:
            source_file_path = absolute_file_path.replace(
                tax_benefit_system.get_package_metadata()["location"], ""
            )
        try:
            source_lines, start_line_number = inspect.getsourcelines(cls)
            source_code = textwrap.dedent("".join(source_lines))
        except (IOError, TypeError):
            source_code, start_line_number = None, None

        return comments, source_file_path, source_code, start_line_number

    def get_formula(self, period=None):
        """
        Returns the formula used to compute the variable at the given period.

        If no period is given and the variable has several formula, return the oldest formula.

        :returns: Formula used to compute the variable

        """

        if not self.formulas:
            return None

        if period is None:
            return self.formulas.peekitem(index=0)[
                1
            ]  # peekitem gets the 1st key-value tuple (the oldest start_date and formula). Return the formula.

        if isinstance(period, Period):
            instant = period.start
        else:
            try:
                instant = periods.period(period).start
            except ValueError:
                instant = periods.instant(period)

        if self.end and instant.date > self.end:
            return None

        instant = str(instant)
        for start_date in reversed(self.formulas):
            if start_date <= instant:
                return self.formulas[start_date]

        return None

    def clone(self):
        clone = self.__class__()
        return clone

    def check_set_value(self, value):
        if self.value_type == Enum and isinstance(value, str):
            try:
                value = self.possible_values[value].index
            except KeyError:
                possible_values = [item.name for item in self.possible_values]
                raise ValueError(
                    "'{}' is not a known value for '{}'. Possible values are ['{}'].".format(
                        value, self.name, "', '".join(possible_values)
                    )
                )
        if self.value_type in (float, int) and isinstance(value, str):
            try:
                value = tools.eval_expression(value)
            except SyntaxError:
                raise ValueError(
                    "I couldn't understand '{}' as a value for '{}'".format(
                        value, self.name
                    )
                )

        try:
            value = numpy.array([value], dtype=self.dtype)[0]
        except (TypeError, ValueError):
            if self.value_type == datetime.date:
                error_message = "Can't deal with date: '{}'.".format(value)
            else:
                error_message = "Can't deal with value: expected type {}, received '{}'.".format(
                    self.json_type, value
                )
            raise ValueError(error_message)
        except (OverflowError):
            error_message = "Can't deal with value: '{}', it's too large for type '{}'.".format(
                value, self.json_type
            )
            raise ValueError(error_message)

        return value

    def default_array(self, array_size):
        array = numpy.empty(array_size, dtype=self.dtype)
        if self.value_type == Enum:
            array.fill(self.default_value.index)
            return EnumArray(array, self.possible_values)
        array.fill(self.default_value)
        return array
