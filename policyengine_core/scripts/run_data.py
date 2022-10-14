import importlib
from argparse import ArgumentParser
from typing import List
from policyengine_core.data.dataset import Dataset
from policyengine_core.scripts import detect_country_package
import pandas as pd


def dataset_summary(datasets: List[Dataset]) -> str:
    years = list(sorted(list(set(sum([ds.years for ds in datasets], [])))))
    df = pd.DataFrame(
        {
            year: ["✓" if year in ds.years else "" for ds in datasets]
            for year in years
        },
        index=[ds.name for ds in datasets],
    )
    df = df.sort_values(by=list(df.columns[::-1]), ascending=False)
    return df.to_markdown(tablefmt="pretty")


def main(parser: ArgumentParser):
    # Get arguments as well as kwargs
    args, kwargs = parser.parse_known_args()
    # Convert kwargs to a dictionary
    kwargs = dict([arg.split("=") for arg in kwargs])

    country_package = args.country_package

    if country_package is None:
        country_package = detect_country_package()

    datasets: List[Dataset] = importlib.import_module(country_package).DATASETS

    if args.dataset == "datasets" and args.action == "list":
        print(dataset_summary(datasets))
        return
    dataset_by_name = {dataset.name: dataset for dataset in datasets}
    dataset = dataset_by_name[args.dataset]

    if args.action == "generate":
        dataset.generate(**kwargs)
    elif args.action == "download":
        dataset.download(**kwargs)
    elif args.action == "upload":
        dataset.upload(**kwargs)
    elif args.action == "remove":
        dataset.remove(**kwargs)
    elif args.action == "list":
        years = dataset.years
        if len(years) == 0:
            print("No saved datasets.")
        else:
            print("Saved datasets:")
            for year in years:
                filepath = dataset.file(year).absolute()
                print(
                    "  * " + filepath.name + "  | " + str(filepath.absolute())
                )
    else:
        raise ValueError(f"Action {args.action} not recognised.")
