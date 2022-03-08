"""Script to get information needed by .conda/meta.yaml from PyPi JSON API.

This script use get_info to get the info (yes !) and replace_in_file to
write them into .conda/meta.yaml.
Sample call:
python3 .github/get_pypi_info.py -p OpenFisca-Country-Template
"""

import argparse
import re

import requests


def get_info(package_name: str = "") -> dict:
    """Get minimal information needed by .conda/meta.yaml from PyPi JSON API.

    ::package_name:: Name of package to get infos from.
    ::return:: A dict with last_version, url and sha256
    """
    if package_name == "":
        raise ValueError("Package name not provided.")
    url = f"https://pypi.org/pypi/{package_name}/json"
    print(f"Calling {url}")
    resp = requests.get(url)
    if resp.status_code != 200:
        raise Exception(f"ERROR calling PyPI ({url}) : {resp}")
    resp = resp.json()
    version = resp["info"]["version"]
    deps_and_version = {}
    for package in resp["info"]["requires_dist"]:
        if "; extra ==" in package:
            continue
        package_name = package.split("(")[0].replace(" ", "")
        package_name = package_name.replace("[pipeline]", "")
        if package_name == "tables":
            package_name = "pytables"
        package_version = (
            re.search("\(([^)]+)", package).group(1).replace(" ", "")  # noqa: W605
        )  # "openfisca-france (>=113.0.2)"
        deps_and_version[package_name] = package_version

    for v in resp["releases"][version]:
        if v["packagetype"] == "sdist":  # for .tag.gz
            return {
                "last_version": version,
                "url": v["url"],
                "sha256": v["digests"]["sha256"],
                "deps_and_version": deps_and_version,
            }
    return {}


def replace_in_file(filepath: str, info: dict):
    """Replace placeholder in meta.yaml by their values.

    ::filepath:: Path to meta.yaml, with filename.
    ::info:: Dict with information to populate.
    """
    with open(filepath, "rt", encoding="utf-8") as fin:
        meta = fin.read()
    # Replace with info from PyPi
    meta = meta.replace("PYPI_VERSION", info["last_version"])
    meta = meta.replace("PYPI_URL", info["url"])
    meta = meta.replace("PYPI_SHA256", info["sha256"])
    deps_and_version = ""
    for name, version in info["deps_and_version"].items():
        deps_and_version += f"    - {name} {version}\n"
    print(f"Adding dependencies to conda:\n{deps_and_version}")
    meta = meta.replace("PYPI_DEPS", deps_and_version)
    with open(filepath, "wt", encoding="utf-8") as fout:
        fout.write(meta)
    print(f"File {filepath} has been updated with info from PyPi.")  # noqa: T001


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-p",
        "--package",
        type=str,
        default="",
        required=True,
        help="The name of the package",
    )
    parser.add_argument(
        "-f",
        "--filename",
        type=str,
        default=".conda/meta.yaml",
        help="Path to meta.yaml, with filename",
    )
    args = parser.parse_args()
    info = get_info(args.package)
    print(
        "Information of the last published PyPi package :", info["last_version"]
    )  # noqa: T001
    replace_in_file(args.filename, info)
