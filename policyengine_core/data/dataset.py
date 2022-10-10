from typing import Callable, Union
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
    label: str = None
    is_openfisca_compatible: bool = True
    data_format: str = None
    folder_path: str = None

    # Data formats
    TABLES = "tables"
    ARRAYS = "arrays"
    TIME_PERIOD_ARRAYS = "time_period_arrays"

    def __init__(self):
        # Setup dataset
        try:
            self.folder_path = Path(self.folder_path)
        except TypeError:
            raise TypeError(
                f"You tried to instantiate {self.label}, but no folder_path attribute has been provided (or an invalid path supplied)."
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
            def wrapper(*args, **kwargs):
                args = list(args)
                args[0] = int(args[0])
                return fn(*args, **kwargs)

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

    @property
    def years(self):
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
