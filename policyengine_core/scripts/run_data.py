import importlib
from argparse import ArgumentParser

from policyengine_core.scripts import detect_country_package


def main(parser: ArgumentParser):
    # Get arguments as well as kwargs
    args, kwargs = parser.parse_known_args()
    # Convert kwargs to a dictionary
    kwargs = dict([arg.split("=") for arg in kwargs])

    country_package = args.country_package

    if country_package is None:
        country_package = detect_country_package()

    datasets = importlib.import_module(country_package).DATASETS

    if args.dataset == "datasets" and args.action == "list":
        print(f"Available datasets for {country_package}:")
        for dataset in datasets:
            print(
                f" - {dataset.name} ({len(dataset().get_saved_datasets())} saved versions)"
            )
        return
    dataset_by_name = {dataset.name: dataset for dataset in datasets}
    dataset = dataset_by_name[args.dataset]()

    if args.action == "build":
        dataset.build(kwargs)
    elif args.action == "download":
        dataset.download(kwargs)
    elif args.action == "upload":
        dataset.upload(kwargs)
    elif args.action == "remove":
        dataset.remove(kwargs)
    elif args.action == "list":
        saved_datasets = dataset.get_saved_datasets()
        if len(saved_datasets) == 0:
            print("No saved datasets.")
        else:
            print("Saved datasets:")
            for saved_dataset in saved_datasets:
                filepath = dataset.get_file_path(saved_dataset)
                config_str = ", ".join(
                    [f"{k}={v}" for k, v in saved_dataset.items()]
                )
                print(
                    "  * "
                    + filepath.name
                    + "  | "
                    + config_str
                    + "  |  "
                    + str(filepath.absolute())
                )
    else:
        raise ValueError(f"Action {args.action} not recognised.")
