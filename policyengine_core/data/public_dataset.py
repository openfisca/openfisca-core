from typing import Dict
from policyengine_core.data.dataset import Dataset
import requests
from tqdm import tqdm


class PublicDataset(Dataset):
    """Datasets inheriting from this class are stored on publicly accessible URLs."""

    url_by_year: Dict[int, str] = None
    """A dictionary mapping years to URLs."""

    def download(self, year: int):
        """Downloads the dataset from the given URL for the given year.

        Args:
            year (int): The year of the dataset to download.
        """
        url = self.url_by_year[year]
        # Download with progress bar
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            total_size = int(r.headers.get("content-length", 0))
            block_size = 1024
            t = tqdm(total=total_size, unit="iB", unit_scale=True)
            with open(self.file(year), "wb") as f:
                for data in r.iter_content(block_size):
                    t.update(len(data))
                    f.write(data)
            t.close()
            if total_size != 0 and t.n != total_size:
                raise Exception(
                    "Downloaded file size does not match content-length header."
                )

    def upload(self, year: int):
        raise AttributeError(
            "Uploading automatically is not supported for public datasets - upload to GitHub releases manually instead."
        )
