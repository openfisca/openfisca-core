from __future__ import annotations

from typing import IO

from openfisca_core.types import TaxBenefitSystem

from pathlib import Path

import openpyxl

from openfisca_core.parameters.parameter_node import ParameterNode
from openfisca_core.parameters.parameter_scale import ParameterScale
from openfisca_core.parameters.parameter_scale_bracket import ParameterScaleBracket
from openfisca_core.reforms import Reform


class ReformExcelBuilder:
    def __init__(
        self,
        baseline_class: type[TaxBenefitSystem],
        path_or_file: Path | str | IO[bytes],
    ) -> None:
        # Le paramètre data_only permet de lire les valeurs calculées des formulas
        self.wb = openpyxl.load_workbook(path_or_file, data_only=True)
        self.baseline_class = baseline_class

    def get_suffixes(self) -> list[str]:
        return [
            sheetname[len("Paramètres") :]
            for sheetname in self.wb.sheetnames
            if sheetname.startswith("Paramètres")
        ]

    @property
    def root_name(self) -> str:
        assert self.wb["Config"]["A2"].value == "root"
        return self.wb["Config"]["B2"].value

    @property
    def period(self) -> str:
        assert self.wb["Config"]["A3"].value == "period"
        return self.wb["Config"]["B3"].value

    def get_parameters(self, suffix: str) -> list[tuple[str, float]]:
        sheet = self.wb[f"Paramètres{suffix}"]
        assert sheet["A1"].value == "Nom"
        assert sheet["B1"].value == "Valeur"

        return [
            (row[0], row[1]) for row in sheet.iter_rows(min_row=2, values_only=True)
        ]

    def build_reform(self, suffix: str) -> "ReformExcel":
        return ReformExcel(
            self.baseline_class(),
            self.root_name,
            self.period,
            self.get_parameters(suffix),
        )


class ReformExcel(Reform):
    """A class representing a reform defined in an Excel file.

    This class extends the Reform class to provide functionality specific to reforms defined in Excel format.
    """

    def __init__(
        self,
        baseline: TaxBenefitSystem,
        root_name: str,
        period: str,
        reformed_parameters: list[tuple[str, str]] | None = None,
    ) -> None:
        """Initialize the ReformExcel instance.

        :param baseline: Baseline TaxBenefitSystem.
        :param path: Path to the Excel file defining the reform.
        :param suffix: Suffix to identify the relevant parameters sheet.
        """
        self.root_name = root_name
        self.period = period
        self.reformed_parameters = reformed_parameters or []
        super().__init__(baseline)

    @staticmethod
    def get_parameter_node(
        p: ParameterNode, segments: str | list[str]
    ) -> tuple[ParameterNode | ParameterScale | ParameterScaleBracket, list[str]]:
        if isinstance(segments, str):
            segments = segments.split(".")
        if segments:
            if hasattr(p, "children"):
                return ReformExcel.get_parameter_node(
                    p.children[segments[0]], segments[1:]
                )
            else:
                return p, segments
        else:
            return p, []

    def apply(self):
        def modify_parameters(local_parameters: ParameterNode) -> ParameterNode:
            # On récupère le nœud racine des paramètres
            root, _ = self.get_parameter_node(local_parameters, self.root_name)
            # Dictionnaire temporaire pour stocker les paramètres à échelons
            # On va le remplir lors du parcours des paramètres de la réforme
            params_with_thresholds: dict[
                str, tuple[ParameterScale, list[tuple[float, ParameterScaleBracket]]]
            ] = dict()

            for name, value in self.reformed_parameters:
                leaf, threshold = self.get_parameter_node(root, name)
                if type(leaf) is ParameterScale:
                    threshold_value = float(".".join(threshold))
                    prop_name = (
                        "amount"
                        if leaf.metadata.get("type") == "single_amount"
                        else "rate"
                    )
                    stripped_name = ".".join(name.split(".")[:-1])

                    bracket = ParameterScaleBracket(
                        data={
                            "threshold": {self.period: {"value": threshold_value}},
                            prop_name: {self.period: {"value": value}},
                        }
                    )

                    params_with_thresholds.setdefault(stripped_name, (leaf, list()))[
                        1
                    ].append(
                        (
                            threshold_value,
                            bracket,
                        )
                    )
                else:
                    leaf.update(start=self.period, value=value)

            for leaf, threshold in params_with_thresholds.values():
                sorted_brackets = [v[1] for v in sorted(threshold, key=lambda x: x[0])]
                leaf.brackets = sorted_brackets

            return local_parameters

        self.modify_parameters(modifier_function=modify_parameters)

    def generate_parameter_tree_values(self, parameter) -> list[tuple[str, float]]:
        values = []
        if type(parameter) is ParameterNode:
            for child in parameter.children.values():
                values.extend(self.generate_parameter_tree_values(child))
        else:
            value = parameter.get_at_instant(self.period)
            name = parameter.name.removeprefix(self.root_name + ".")
            if type(parameter) is ParameterScale:
                threshold_values = (
                    value.amounts
                    if parameter.metadata.get("type") == "single_amount"
                    else value.rates
                )
                for threshold, val in zip(value.thresholds, threshold_values):
                    values.append((f"{self.root_name}.{name}.{threshold}", val))
            else:
                values.append((name, value))
        return sorted(values, key=lambda v: v[0])

    @property
    def parameter_data(self) -> list[tuple[str, float]]:
        root_parameter, _ = self.get_parameter_node(self.parameters, self.root_name)
        return self.generate_parameter_tree_values(root_parameter)

    def generate_template_xlsx(self, path_or_file: Path | str | IO[bytes]) -> None:
        wb = openpyxl.Workbook()
        ws_config = wb.active
        ws_config.title = "Config"
        ws_config["A1"] = "Parameter name"
        ws_config["B1"] = "Parameter value"
        ws_config["A2"] = "root"
        ws_config["B2"] = self.root_name
        ws_config["A3"] = "period"
        ws_config["B3"] = self.period

        ws_params = wb.create_sheet(title="Paramètres")
        ws_params["A1"] = "Nom"
        ws_params["B1"] = "Valeur"

        for i, (name, value) in enumerate(self.parameter_data, start=2):
            ws_params[f"A{i}"] = name
            ws_params[f"B{i}"] = value

        wb.save(path_or_file)
