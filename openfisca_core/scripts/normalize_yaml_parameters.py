#! /usr/bin/env python


"""Normalize a YAML parameter tree, loading it from a directory and re-writing it to another one.

This allows in particular to ensure that each YAML file contains exactly one parameter.
"""


import argparse
import logging
from pathlib import Path
import sys

from openfisca_core.parameters import load_parameter_file, Parameter, ParameterNode, save_parameters_to_dir


logger = logging.getLogger(__name__)


def check_path_length(base_dir, max_path_length):
    for path in base_dir.rglob("*.yaml"):
        relative_path = path.relative_to(base_dir)
        relative_path_len = len(str(relative_path))
        if relative_path_len > max_path_length:
            logger.error("%r length is %d but max length is %d", str(relative_path), relative_path_len, max_path_length)


def main():
    parser = argparse.ArgumentParser(description = __doc__)
    parser.add_argument('--max-path-length', type = int, default = None,
                        help = "log error if path is longer than specified value")
    parser.add_argument('-v', '--verbose', action = 'store_true', default = False, help = "increase output verbosity")
    parser.add_argument('source_dir', type = Path, help = "directory with parameters to read")
    parser.add_argument('target_dir', type = Path, help = "directory where parameters are written")
    args = parser.parse_args()

    if not args.source_dir.is_dir():
        parser.error("Invalid source_dir")
    if not args.target_dir.is_dir():
        args.target_dir.mkdir()

    logging.basicConfig()

    parameters = load_parameter_file(args.source_dir)
    save_parameters_to_dir(parameters, args.target_dir)

    if args.max_path_length is not None:
        check_path_length(base_dir = args.target_dir, max_path_length = args.max_path_length)

if __name__ == "__main__":
    sys.exit(main())
