# flake8: noqa T001

import argparse
import glob
import os

from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedSeq

from openfisca_core.scripts import (
    add_tax_benefit_system_arguments,
    build_tax_benefit_system,
)

yaml = YAML()
yaml.default_flow_style = False
yaml.width = 4096

TEST_METADATA = {
    "period",
    "name",
    "reforms",
    "only_variables",
    "ignore_variables",
    "absolute_error_margin",
    "relative_error_margin",
    "description",
    "keywords",
}


def build_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "path",
        help="paths (files or directories) of tests to execute",
        nargs="+",
    )
    return add_tax_benefit_system_arguments(parser)


class Migrator:
    def __init__(self, tax_benefit_system) -> None:
        self.tax_benefit_system = tax_benefit_system
        self.entities_by_plural = {
            entity.plural: entity for entity in self.tax_benefit_system.entities
        }

    def migrate(self, path) -> None:
        if isinstance(path, list):
            for item in path:
                self.migrate(item)
            return

        if os.path.isdir(path):
            yaml_paths = glob.glob(os.path.join(path, "*.yaml"))
            subdirectories = glob.glob(os.path.join(path, "*/"))

            for yaml_path in yaml_paths:
                self.migrate(yaml_path)

            for subdirectory in subdirectories:
                self.migrate(subdirectory)

            return

        with open(path) as yaml_file:
            tests = yaml.safe_load(yaml_file)
        if isinstance(tests, CommentedSeq):
            migrated_tests = [self.convert_test(test) for test in tests]
        else:
            migrated_tests = self.convert_test(tests)

        with open(path, "w") as yaml_file:
            yaml.dump(migrated_tests, yaml_file)

    def convert_test(self, test):
        if test.get("output"):
            # This test is already converted, ignoring it
            return test
        result = {}
        outputs = test.pop("output_variables")
        inputs = test.pop("input_variables", {})
        for key, value in test.items():
            if key in TEST_METADATA:
                result[key] = value
            else:
                inputs[key] = value
        result["input"] = self.convert_inputs(inputs)
        result["output"] = outputs
        return result

    def convert_inputs(self, inputs):
        first_key = next(iter(inputs.keys()), None)
        if first_key not in self.entities_by_plural:
            return inputs
        results = {}
        for entity_plural, entities_description in inputs.items():
            entity = self.entities_by_plural[entity_plural]
            if not isinstance(entities_description, (CommentedSeq, list)):
                entities_description = [entities_description]
            if not entity.is_person and len(entities_description) == 1:
                results[entity.key] = remove_id(entities_description[0])
                continue
            results[entity_plural] = self.convert_entities(entity, entities_description)

        return self.generate_missing_entities(results)

    def convert_entities(self, entity, entities_description):
        return {
            entity_description.get("id", f"{entity.key}_{index}"): remove_id(
                entity_description,
            )
            for index, entity_description in enumerate(entities_description)
        }

    def generate_missing_entities(self, inputs):
        for entity in self.tax_benefit_system.entities:
            if entity.plural in inputs or entity.key in inputs:
                continue
            persons = inputs[self.tax_benefit_system.person_entity.plural]
            if len(persons) == 1:
                person_id = next(iter(persons))
                inputs[entity.key] = {
                    entity.roles[0].plural or entity.roles[0].key: [person_id],
                }
            else:
                inputs[entity.plural] = {
                    f"{entity.key}_{index}": {
                        entity.roles[0].plural or entity.roles[0].key: [person_id],
                    }
                    for index, person_id in enumerate(persons.keys())
                }
        return inputs


def remove_id(input_dict):
    return {key: value for (key, value) in input_dict.items() if key != "id"}


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    paths = [os.path.abspath(path) for path in args.path]

    tax_benefit_system = build_tax_benefit_system(
        args.country_package,
        args.extensions,
        args.reforms,
    )

    Migrator(tax_benefit_system).migrate(paths)


if __name__ == "__main__":
    main()
