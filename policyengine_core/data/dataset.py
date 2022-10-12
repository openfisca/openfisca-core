import importlib
from typing import Callable, Dict, List, Union
import logging
import os
from pathlib import Path
import re
import pandas as pd
import h5py
import numpy as np
from policyengine_core.periods import Period, period
from policyengine_core.types import ArrayLike


class Dataset:
    """The `Dataset` class is a base class to represent the data required to
    run a microsimulation representative of a large set of entities.
    """

    name: str = None
    label: str = None
    options: dict = None
    country_package_name: str = (
        None  # Used to decide where to store the microdata files.
    )

    def __init__(self):
        if self.options is None:
            self.options = {}

    def build(self, options: dict = None) -> None:
        """Builds the microdata from raw data. Include implementation logic here.
        Use `self.options` for default options, and `options` for user-defined options.
        At the end, use `self.write` to write the microdata to a file. For example:

        employment_income_in_2022 = [100, 200, 300]
        self.write({"employment_income": {period("2022"): employment_income_in_2022}})
        """
        raise NotImplementedError()

    def write(self, inputs: Dict[str, Dict[Period, ArrayLike]]) -> None:
        """Writes microdata values to a standardised microdata file for this dataset.

        Args:
            inputs (Dict[str, Dict[Period, ArrayLike]]): A dictionary of microdata values to write, keyed by variable name, then time period.
        """

        file_path = self.get_file_path()

        with h5py.File(file_path, "w") as f:
            for variable, values in inputs.items():
                for period, value in values.items():
                    f.create_dataset(f"{variable}/{str(period)}", data=value)

    def exists(self, options: dict = None) -> bool:
        """Checks if the microdata file exists.

        Args:
            options (dict, optional): The options to use to generate the filename. Defaults to None.

        Returns:
            bool: True if the file exists, False otherwise.
        """
        file_path = self.get_file_path(options)
        return file_path.exists()

    def load(self, options: dict = None) -> Dict[str, Dict[Period, ArrayLike]]:
        """Loads the microdata from the file.

        Args:
            options (dict, optional): The options to use to generate the filename. Defaults to None.

        Returns:
            Dict[str, Dict[Period, ArrayLike]]: A dictionary of microdata values, keyed by variable name, then time period.
        """
        file_path = self.get_file_path(options)

        if not file_path.exists():
            raise FileNotFoundError(
                f"Microdata file {file_path} does not exist. Please run `build` to generate the microdata file."
            )

        with h5py.File(file_path, "r") as f:
            return {
                variable: {
                    period_string: f[f"{variable}/{period_string}"][:]
                    for period_string in f[variable]
                }
                for variable in f
            }

    def get_file_path(self, options: dict = None) -> Path:
        """Returns the file path for the microdata file.

        Args:
            options (dict, optional): The options to use to generate the filename. Defaults to None.

        Returns:
            Path: The file path for the microdata file.
        """

        try:
            # Import the country package to get the country package name.
            country_package = importlib.import_module(
                self.country_package_name
            )
            country_dir = country_package.COUNTRY_DIR
        except:
            raise ValueError(
                f"Could not import the country package {self.country_package_name}."
            )

        # Convert the options {x: y} to a string "x_y".

        if options is None:
            options = self.options
        else:
            options = {**self.options, **options}

        options_string = "_".join([f"{k}-{v}" for k, v in options.items()])
        if len(options_string) > 0:
            options_string = f"_{options_string}"
        filename = f"{self.name}{options_string}.h5"

        folder = country_dir / "data" / "microdata"
        folder.mkdir(parents=True, exist_ok=True)

        return folder / filename

    def get_saved_datasets(self) -> List[dict]:
        """Returns a list of saved datasets that match the current dataset name and country package.

        Returns:
            List[dict]: A list of saved datasets that match the current dataset name and country package.
        """
        try:
            # Import the country package to get the country package name.
            country_package = importlib.import_module(
                self.country_package_name
            )
            country_dir = country_package.COUNTRY_DIR
        except:
            raise ValueError(
                f"Could not import the country package {self.country_package_name}."
            )

        folder = country_dir / "data" / "microdata"
        folder.mkdir(parents=True, exist_ok=True)

        saved_datasets = []
        for file in folder.glob(f"{self.name}*.h5"):
            options = {}
            options_string = re.search(
                rf"{self.name}_(.*)\.h5", file.name
            ).group(1)
            for option in options_string.split("_"):
                if option != "":
                    key, value = option.split("-")
                    options[key] = value
            saved_datasets.append(options)

        return saved_datasets

    def remove(self, options: dict = None) -> None:
        """Removes the microdata file.

        Args:
            options (dict, optional): The options to use to generate the filename. Defaults to None.
        """
        file_path = self.get_file_path(options)
        if file_path.exists():
            file_path.unlink()

    def remove_all(self) -> None:
        """Removes all microdata files for this dataset."""
        for options in self.get_saved_datasets():
            self.remove(options)
