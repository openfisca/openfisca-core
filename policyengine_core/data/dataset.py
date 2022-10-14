import importlib
from typing import Callable, Dict, Union
import logging
import os
from pathlib import Path
import re
import pandas as pd
import h5py
import numpy as np


class Dataset:
    """The `Dataset` class is a base class for datasets used directly or indirectly for OpenFisca models.
    A dataset defines a generation function to create it from other data, and this class provides common features
    like cloud storage, metadata and loading."""

    name: str = None
    """The name of the dataset. This is used to generate filenames and is used as the key in the `datasets` dictionary."""
    label: str = None
    """The label of the dataset. This is used for logging and is used as the key in the `datasets` dictionary."""
    is_openfisca_compatible: bool = True
    """Whether the dataset is compatible with OpenFisca. If True, the dataset will be stored as a collection of arrays. If False, the dataset will be stored as a collection of tables."""
    data_format: str = None
    """The format of the dataset. This can be either `Dataset.ARRAYS`, `Dataset.TIME_PERIOD_ARRAYS` or `Dataset.TABLES`. If `Dataset.ARRAYS`, the dataset is stored as a collection of arrays. If `Dataset.TIME_PERIOD_ARRAYS`, the dataset is stored as a collection of arrays, with one array per time period. If `Dataset.TABLES`, the dataset is stored as a collection of tables (DataFrames)."""
    folder_path: str = None
    """The path to the folder where the dataset is stored (in .h5 files)."""

    # Data formats
    TABLES = "tables"
    ARRAYS = "arrays"
    TIME_PERIOD_ARRAYS = "time_period_arrays"

    def __init__(self):
        # Setup dataset
        if self.folder_path is None:
            raise ValueError(
                "Dataset folder_path must be specified in the dataset class definition."
            )

        if not self.folder_path.exists():
            logging.info(
                f"Creating folder {self.folder_path} for {self.label} dataset."
            )
            self.folder_path.mkdir(parents=True)

        assert (
            self.name
        ), "You tried to instantiate a Dataset object, but no name has been provided."
        assert (
            self.label
        ), "You tried to instantiate a Dataset object, but no label has been provided."

        if self.data_format is None:
            if not self.is_openfisca_compatible:
                # Assume that external (raw) datasets are a collection of tables.
                self.data_format = Dataset.TABLES
            else:
                # OpenFisca datasets are a collection of arrays.
                self.data_format = Dataset.ARRAYS

        assert self.data_format in [
            Dataset.TABLES,
            Dataset.ARRAYS,
            Dataset.TIME_PERIOD_ARRAYS,
        ], "You tried to instantiate a Dataset object, but your data_format attribute is invalid."

        # Ensure typed arguments are enforced in `generate`

        def cast_first_arg_as_int(fn: Callable) -> Callable:
            def wrapper(year: str, *args, **kwargs):
                year = int(year)
                return fn(year, *args, **kwargs)

            return wrapper

        self.generate = cast_first_arg_as_int(self.generate)
        self.download = cast_first_arg_as_int(self.download)
        self.upload = cast_first_arg_as_int(self.upload)

    def filename(self, year: int) -> str:
        """Returns the filename of the dataset for a given year.

        Args:
            year (int): The year of the dataset to generate.

        Returns:
            str: The filename of the dataset.
        """
        return f"{self.name}_{year}.h5"

    def file(self, year: int) -> Path:
        """Returns the path to the dataset for a given year.

        Args:
            year (int): The year of the dataset to generate.

        Returns:
            Path: The path to the dataset.
        """
        return self.folder_path / self.filename(year)

    def load(
        self, year: int, key: str = None, mode: str = "r"
    ) -> Union[h5py.File, np.array, pd.DataFrame, pd.HDFStore]:
        """Loads the dataset for a given year, returning a H5 file reader. You can then access the
        dataset like a dictionary (e.g.e Dataset.load(2022)["variable"]).

        Args:
            year (int): The year of the dataset to load.
            key (str, optional): The key to load. Defaults to None.
            mode (str, optional): The mode to open the file with. Defaults to "r".

        Returns:
            Union[h5py.File, np.array, pd.DataFrame, pd.HDFStore]: The dataset.
        """
        file = self.folder_path / self.filename(year)
        if self.data_format in (Dataset.ARRAYS, Dataset.TIME_PERIOD_ARRAYS):
            if key is None:
                # If no key provided, return the basic H5 reader.
                return h5py.File(file, mode=mode)
            else:
                # If key provided, return only the values requested.
                with h5py.File(file, mode=mode) as f:
                    values = np.array(f[key])
                return values
        elif self.data_format == Dataset.TABLES:
            if key is None:
                # Non-openfisca datasets are assumed to be of the format (table name: [table], ...).
                return pd.HDFStore(file)
            else:
                # If a table name is provided, return that table.
                with pd.HDFStore(file) as f:
                    values = f[key]
                return values
        else:
            raise ValueError(
                f"Invalid data format {self.data_format} for dataset {self.label}."
            )

    def save(self, year: int, key: str, values: Union[np.array, pd.DataFrame]):
        """Overwrites the values for `key` with `values`.

        Args:
            year (int): The year of the dataset to save.
            key (str): The key to save.
            values (Union[np.array, pd.DataFrame]): The values to save.
        """
        file = self.folder_path / self.filename(year)
        if self.data_format in (Dataset.ARRAYS, Dataset.TIME_PERIOD_ARRAYS):
            with h5py.File(file, "a") as f:
                # Overwrite if existing
                if key in f:
                    del f[key]
                f.create_dataset(key, data=values)
        elif self.data_format == Dataset.TABLES:
            with pd.HDFStore(file, "a") as f:
                f.put(key, values)
        else:
            raise ValueError(
                f"Invalid data format {self.data_format} for dataset {self.label}."
            )

    def save_variable_values(
        self, year: int, data: Dict[str, Dict[str, np.array]]
    ) -> None:
        """Writes data values for variables in specific time periods.

        Args:
            year (int): The year of the dataset to save.
            data (Dict[str, Dict[str, np.array]]): The data to save. Should be nested in the form {variable_name: {time_period: values}}.
        """
        if self.data_format is not self.TIME_PERIOD_ARRAYS:
            raise ValueError(
                f"Invalid data format {self.data_format} for dataset {self.label}."
            )

        file = self.folder_path / self.filename(year)
        with h5py.File(file, "a") as f:
            for variable, values in data.items():
                for time_period, value in values.items():
                    key = f"{variable}/{time_period}"
                    # Overwrite if existing
                    if key in f:
                        del f[key]
                    f.create_dataset(key, data=value)

    def keys(self, year: int):
        """Returns the keys of the dataset for a given year.

        Args:
            year (int): The year of the dataset to generate.

        Returns:
            list: The keys of the dataset.
        """
        if self.data_format in (Dataset.ARRAYS, Dataset.TIME_PERIOD_ARRAYS):
            with h5py.File(self.file(year), mode="r") as f:
                return list(f.keys())
        elif self.data_format == Dataset.TABLES:
            with pd.HDFStore(self.file(year)) as f:
                return list(f.keys())
        else:
            raise ValueError(
                f"Invalid data format {self.data_format} for dataset {self.label}."
            )

    def generate(self, year: int):
        """Generates the dataset for a given year (all datasets should implement this method).

        Args:
            year (int): The year of the dataset to generate.

        Raises:
            NotImplementedError: If the function has not been overriden.
        """
        raise NotImplementedError(
            f"You tried to generate the dataset for year {year} of {self.label}, but no dataset generation implementation has been provided for {self.label}."
        )

    def download(self, year: int):
        """Downloads the dataset for a given year (all datasets should implement this method).

        Args:
            year (int): The year of the dataset to download.

        Raises:
            NotImplementedError: If the function has not been overriden.
        """
        raise NotImplementedError(
            f"You tried to download the dataset for year {year} of {self.label}, but no dataset download implementation has been provided for {self.label}."
        )

    def upload(self, year: int):
        """Uploads the dataset for a given year (all datasets should implement this method).

        Args:
            year (int): The year of the dataset to upload.

        Raises:
            NotImplementedError: If the function has not been overriden.
        """
        raise NotImplementedError(
            f"You tried to upload the dataset for year {year} of {self.label}, but no dataset upload implementation has been provided for {self.label}."
        )

    def remove(self, year: int = None):
        """Removes the dataset file for a given year.

        Args:
            year (int, optional): The year of the dataset to remove. Defaults to all.
        """
        if year is None:
            filenames = map(self.filename(year), self.years)
        else:
            filenames = (self.filename(year),)
        for filename in filenames:
            filepath = self.folder_path / filename
            if filepath.exists():
                os.remove(filepath)

    def remove_all(self):
        """Removes all dataset files."""
        for year in self.years:
            self.remove(year)

    @property
    def years(self):
        """Returns the years for which the dataset has been generated."""
        pattern = re.compile(f"\n{self.name}_([0-9]+).h5")
        return list(
            map(
                int,
                pattern.findall(
                    "\n"
                    + "\n".join(
                        map(lambda path: path.name, self.folder_path.iterdir())
                    )
                ),
            )
        )
