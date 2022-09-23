# flake8: noqa T001

import fnmatch
import os
import sys
import warnings

try:
    from bs4 import BeautifulSoup

except ImportError:
    message = [
        "You tried to use the 'bs4' package, but it is not currently",
        "installed. Try running `pip install --user bs4`.",
        ]
    warnings.warn(" ".join(message), UserWarning)


def find_param_files(input_dir):
    param_files = []
    for root, _dirnames, filenames in os.walk(input_dir):
        for filename in fnmatch.filter(filenames, "*.xml"):
            param_files.append(os.path.join(root, filename))

    return param_files


def find_placeholders(file_path):
    with open(file_path, encoding = "utf-8") as file:
        xml_content = file.read()

    xml_parsed = BeautifulSoup(xml_content, "lxml-xml")

    placeholders = xml_parsed.find_all("PLACEHOLDER")

    output_list = []
    for placeholder in placeholders:
        parent_list = list(placeholder.parents)[:-1]
        path = ".".join([p.attrs["code"] for p in parent_list if "code" in p.attrs][::-1])

        deb = placeholder.attrs["deb"]

        output_list.append((deb, path))

    output_list = sorted(output_list, key = lambda x: x[0])

    return output_list


if __name__ == "__main__":
    print("""find_placeholders.py : Find nodes PLACEHOLDER in xml parameter files
Usage :
    python find_placeholders /dir/to/search
""")

    assert len(sys.argv) == 2
    input_dir = sys.argv[1]

    param_files = find_param_files(input_dir)

    for filename_input in param_files:
        output_list = find_placeholders(filename_input)

        print(f"File {filename_input}")

        for deb, path in output_list:
            print(f"{deb} {path}")

        print("\n")
