from __future__ import annotations

from typing import Dict, List, Optional

import copy
import os

from policyengine_core import commons, periods
from policyengine_core.errors import ParameterParsingError
from policyengine_core.parameters import (
    config,
    helpers,
    AtInstantLike,
    ParameterAtInstant,
)


class Parameter(AtInstantLike):
    """A parameter of the legislation.

    Parameters can change over time.

    Attributes:
        values_list: List of the values, in reverse chronological order.


    Args:
        name: Name of the parameter, e.g. "taxes.some_tax.some_param".
        data: Data loaded from a YAML file.
        file_path: File the parameter was loaded from.

    Instantiate a parameter without metadata:

    >>>  Parameter('rate', data = {
            "2015-01-01": 550,
            "2016-01-01": 600
            })

    Instantiate a parameter with metadata:

    >>>  Parameter('rate', data = {
            'description': 'Income tax rate applied on salaries',
            'values': {
                "2015-01-01": {'value': 550, 'metadata': {'reference': 'http://taxes.gov/income_tax/2015'}},
                "2016-01-01": {'value': 600, 'metadata': {'reference': 'http://taxes.gov/income_tax/2016'}}
                }
            })

    """

    def __init__(
        self, name: str, data: dict, file_path: Optional[str] = None
    ) -> None:
        self.name: str = name
        self.file_path: Optional[str] = file_path
        helpers._validate_parameter(self, data, data_type=dict)
        self.description: Optional[str] = None
        self.metadata: Dict = {}
        self.documentation: Optional[str] = None

        # Normal parameter declaration: the values are declared under the 'values' key: parse the description and metadata.
        if data.get("values"):
            # 'unit' and 'reference' are only listed here for backward compatibility
            self.metadata.update(data.get("metadata", {}))
            helpers._validate_parameter(
                self, data, allowed_keys=config.COMMON_KEYS.union({"values"})
            )
            self.description = data.get("description")

            helpers._validate_parameter(self, data["values"], data_type=dict)
            values = data["values"]

            self.documentation = data.get("documentation")

        else:  # Simplified parameter declaration: only values are provided
            values = data

        instants = sorted(
            values.keys(), reverse=True
        )  # sort in reverse chronological order

        values_list = []
        for instant_str in instants:
            if not periods.INSTANT_PATTERN.match(instant_str):
                raise ParameterParsingError(
                    "Invalid property '{}' in '{}'. Properties must be valid YYYY-MM-DD instants, such as 2017-01-15.".format(
                        instant_str, self.name
                    ),
                    file_path,
                )

            instant_info = values[instant_str]

            #  Ignore expected values, as they are just metadata
            if (
                instant_info == "expected"
                or isinstance(instant_info, dict)
                and instant_info.get("expected")
            ):
                continue

            value_name = helpers._compose_name(name, item_name=instant_str)
            value_at_instant = ParameterAtInstant(
                value_name,
                instant_str,
                data=instant_info,
                file_path=self.file_path,
                metadata=self.metadata,
            )
            values_list.append(value_at_instant)

        self.values_list: List[ParameterAtInstant] = values_list

    def __repr__(self):
        return os.linesep.join(
            [
                "{}: {}".format(
                    value.instant_str,
                    value.value if value.value is not None else "null",
                )
                for value in self.values_list
            ]
        )

    def __eq__(self, other):
        return (self.name == other.name) and (
            self.values_list == other.values_list
        )

    def clone(self):
        clone = commons.empty_clone(self)
        clone.__dict__ = self.__dict__.copy()

        clone.metadata = copy.deepcopy(self.metadata)
        clone.values_list = [
            parameter_at_instant.clone()
            for parameter_at_instant in self.values_list
        ]
        return clone

    def update(self, period=None, start=None, stop=None, value=None):
        """
        Change the value for a given period.

        :param period: Period where the value is modified. If set, `start` and `stop` should be `None`.
        :param start: Start of the period. Instance of `policyengine_core.periods.Instant`. If set, `period` should be `None`.
        :param stop: Stop of the period. Instance of `policyengine_core.periods.Instant`. If set, `period` should be `None`.
        :param value: New value. If `None`, the parameter is removed from the legislation parameters for the given period.
        """
        if period is not None:
            if start is not None or stop is not None:
                raise TypeError(
                    "Wrong input for 'update' method: use either 'update(period, value = value)' or 'update(start = start, stop = stop, value = value)'. You cannot both use 'period' and 'start' or 'stop'."
                )
            if isinstance(period, str):
                period = periods.period(period)
            start = period.start
            stop = period.stop
        if start is None:
            raise ValueError("You must provide either a start or a period")
        start_str = str(start)
        stop_str = str(stop.offset(1, "day")) if stop else None

        old_values = self.values_list
        new_values = []
        n = len(old_values)
        i = 0

        # Future intervals : not affected
        if stop_str:
            while (i < n) and (old_values[i].instant_str >= stop_str):
                new_values.append(old_values[i])
                i += 1

        # Right-overlapped interval
        if stop_str:
            if new_values and (stop_str == new_values[-1].instant_str):
                pass  # such interval is empty
            else:
                if i < n:
                    overlapped_value = old_values[i].value
                    value_name = helpers._compose_name(
                        self.name, item_name=stop_str
                    )
                    new_interval = ParameterAtInstant(
                        value_name, stop_str, data={"value": overlapped_value}
                    )
                    new_values.append(new_interval)
                else:
                    value_name = helpers._compose_name(
                        self.name, item_name=stop_str
                    )
                    new_interval = ParameterAtInstant(
                        value_name, stop_str, data={"value": None}
                    )
                    new_values.append(new_interval)

        # Insert new interval
        value_name = helpers._compose_name(self.name, item_name=start_str)
        new_interval = ParameterAtInstant(
            value_name, start_str, data={"value": value}
        )
        new_values.append(new_interval)

        # Remove covered intervals
        while (i < n) and (old_values[i].instant_str >= start_str):
            i += 1

        # Past intervals : not affected
        while i < n:
            new_values.append(old_values[i])
            i += 1

        self.values_list = new_values

    def get_descendants(self):
        return iter(())

    def _get_at_instant(self, instant):
        for value_at_instant in self.values_list:
            if value_at_instant.instant_str <= instant:
                return value_at_instant.value
        return None
