import logging
import subprocess
import warnings
from typing import Dict

from policyengine_core.data.dataset import Dataset


class PrivateDataset(Dataset):
    """Private datasets are stored on Google Cloud Buckets (requires the Google Cloud CLI to be installed)."""

    bucket_name: str
    """The name of the Google Cloud Storage bucket to use for this dataset."""
    filename_by_year: Dict[int, str] = None
    """A dictionary mapping years to filenames."""

    def _get_storage_bucket(self):
        from google.cloud import storage

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            try:
                client = storage.Client()
            except:
                logging.info(
                    "Could not automatically authenticate with Google Cloud, prompting login..."
                )
                failed_login = subprocess.check_call(
                    ["gcloud auth application-default login"],
                    shell=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                if not failed_login:
                    logging.info(
                        "Successfully logged in to Google Cloud, attempting to download..."
                    )
                    client = storage.Client()
                else:
                    raise Exception(
                        "Could not authenticate with Google Cloud."
                    )
        try:
            return client.get_bucket(self.bucket_name)
        except Exception as e:
            raise Exception(
                f"Your account does not have sufficient permissions: {e}."
            )

    def download(self, year: int):
        """Downloads the dataset from Google Cloud Storage for the given year. Overwrites any existing dataset for the year specified.

        Args:
            year (int): The year of the dataset to download.

        Raises:
            FileNotFoundError: If the dataset could not be found on Google Cloud Storage.
        """
        bucket = self._get_storage_bucket()
        filenames = list(map(lambda blob: blob.name, bucket.list_blobs()))
        filename = self.filename_by_year[year]

        if filename not in filenames:
            raise FileNotFoundError(
                f"Could not find {filename} in the {self.bucket_name} bucket."
            )

        blob = bucket.blob(filename)
        with open(self.file(year), "wb") as f:
            blob.download_to_file(f)

        logging.info("Successfully downloaded and saved dataset.")

    def upload(self, year: int, filename: str = None):
        """Uploads the dataset to Google Cloud Storage for the given year.

        Args:
            year (int): The year of the dataset to upload.
        """
        bucket = self._get_storage_bucket()
        if filename is None:
            # Overwriting existing dataset - check this is intended with a prompt.

            if year in self.filename_by_year.keys():
                overwrite = input(
                    f"Are you sure you want to overwrite the existing dataset for year {year}? (y/n): "
                )
                if overwrite.lower() != "y":
                    raise Exception("Upload cancelled.")
            filename = self.filename_by_year[year]
            overwriting_existing = True
        else:
            overwriting_existing = False

        blob = bucket.blob(filename)
        blob.upload_from_filename(self.file(year))

        logging.info("Successfully uploaded dataset.")

        if overwriting_existing:
            logging.info(
                f"You have overwritten the existing {filename} file. Anyone using this dataset will transition to the new dataset automatically when they next download the file."
            )
        else:
            logging.info(
                f"You have uploaded a new file, {filename}, to the {self.bucket_name} bucket. Users will not automatically upgrade, unless you add the filename {filename} to the `filename_by_year` dictionary in this dataset."
            )
