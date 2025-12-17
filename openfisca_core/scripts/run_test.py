import logging
import os
import sys

from openfisca_core.scripts import build_tax_benefit_system
from openfisca_core.tools.test_runner import run_tests


def main(parser) -> None:
    args = parser.parse_args()
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.WARNING,
        stream=sys.stdout,
    )

    tax_benefit_system = build_tax_benefit_system(
        args.country_package,
        args.extensions,
        args.reforms,
    )

    options = {
        "country_package": args.country_package,
        "extensions": args.extensions,
        "reforms": args.reforms,
        "pdb": args.pdb,
        "performance_graph": args.performance_graph,
        "performance_tables": args.performance_tables,
        "verbose": args.verbose,
        "aggregate": args.aggregate,
        "max_depth": args.max_depth,
        "name_filter": args.name_filter,
        "only_variables": args.only_variables,
        "ignore_variables": args.ignore_variables,
    }

    paths = [os.path.abspath(path) for path in args.path]

    # Parallel mode
    if args.in_parallel:
        from openfisca_core.tools.test_runner import run_tests_in_parallel

        return sys.exit(
            run_tests_in_parallel(
                tax_benefit_system, paths, options, args.num_workers, args.verbose
            )
        )

    # Default serial mode
    sys.exit(run_tests(tax_benefit_system, paths, options))
