# flake8: noqa T001

import fnmatch
import os
import sys

from bs4 import BeautifulSoup


def find_param_files(input_dir):
    param_files = []
    for root, _dirnames, filenames in os.walk(input_dir):
        for filename in fnmatch.filter(filenames, "*.xml"):
            param_files.append(os.path.join(root, filename))

    return param_files


def find_placeholders(filename_input):
    with open(filename_input) as f:
        xml_content = f.read()

    xml_parsed = BeautifulSoup(xml_content, "lxml-xml")

    placeholders = xml_parsed.find_all("PLACEHOLDER")

    output_list = []
    for placeholder in placeholders:
        parent_list = list(placeholder.parents)[:-1]
        path = ".".join(
            [p.attrs["code"] for p in parent_list if "code" in p.attrs][::-1],
        )

        deb = placeholder.attrs["deb"]

        output_list.append((deb, path))

    return sorted(output_list, key=lambda x: x[0])


if __name__ == "__main__":
    assert len(sys.argv) == 2
    input_dir = sys.argv[1]

    param_files = find_param_files(input_dir)

    for filename_input in param_files:
        output_list = find_placeholders(filename_input)

        for _deb, _path in output_list:
            pass
