from datetime import date
from typing import IO

import io

import openpyxl
import pytest

from openfisca_core.parameters.parameter_scale import ParameterScale
from openfisca_core.reforms.reform_excel import ReformExcel, ReformExcelBuilder


def to_wb_file(wb: openpyxl.Workbook) -> IO[bytes]:
    bytes = io.BytesIO()
    wb.save(bytes)
    bytes.seek(0)
    return bytes


class TestExcel:
    @pytest.fixture
    def wb(self):
        wb = openpyxl.Workbook()
        config_sheet = wb.create_sheet("Config")
        wb.create_sheet("Paramètres")
        wb.create_sheet("OtherSheet")
        config_sheet["A2"] = "root"
        config_sheet["B2"] = "benefits"
        config_sheet["A3"] = "period"
        config_sheet["B3"] = "2025-01-01"

        param_sheet = wb.create_sheet("Paramètres_2025")
        param_sheet["A1"] = "Nom"
        param_sheet["B1"] = "Valeur"
        param_sheet.append(["parenting_allowance.amount", 100000])

        return wb

    @pytest.fixture
    def wb_file(self, wb: openpyxl.Workbook) -> IO[bytes]:
        return to_wb_file(wb)

    class TestReformExcelBuilder:
        def test_get_suffixes(self, wb_file):
            builder = ReformExcelBuilder(baseline_class=None, path_or_file=wb_file)
            suffixes = builder.get_suffixes()
            assert suffixes == ["", "_2025"]

        def test_get_reform_data(self, wb_file):
            builder = ReformExcelBuilder(baseline_class=None, path_or_file=wb_file)

            assert builder.root_name == "benefits"
            assert builder.period == "2025-01-01"
            assert builder.get_parameters("_2025") == [
                ("parenting_allowance.amount", 100000, None)
            ]

        def test_build_reform(self, tax_benefit_system_class, wb_file):
            builder = ReformExcelBuilder(
                baseline_class=tax_benefit_system_class, path_or_file=wb_file
            )
            reform = builder.build_reform("_2025")

            assert reform.root_name == "benefits"
            assert reform.period == "2025-01-01"
            assert reform.reformed_parameters == [
                ("parenting_allowance.amount", 100000, None)
            ]

        def test_pas_de_root(self, tax_benefit_system_class, wb):
            ws = wb["Config"]
            ws.delete_rows(2)

            builder = ReformExcelBuilder(
                baseline_class=tax_benefit_system_class, path_or_file=to_wb_file(wb)
            )
            with pytest.raises(AssertionError):
                builder.build_reform("_2025")

        def test_pas_de_period(self, tax_benefit_system_class, wb):
            ws = wb["Config"]
            ws.delete_rows(3)

            builder = ReformExcelBuilder(
                baseline_class=tax_benefit_system_class, path_or_file=to_wb_file(wb)
            )
            with pytest.raises(AssertionError):
                builder.build_reform("_2025")

        def test_get_parameters_shuffled_columns(self, wb):
            param_sheet = wb["Paramètres_2025"]
            # Shuffle columns
            for row in param_sheet.iter_rows():
                row[0].value, row[1].value = row[1].value, row[0].value

            builder = ReformExcelBuilder(
                baseline_class=None, path_or_file=to_wb_file(wb)
            )
            assert builder.get_parameters("_2025") == [
                ("parenting_allowance.amount", 100000, None)
            ]

        def test_get_parameters_with_date(self, wb):
            param_sheet = wb["Paramètres_2025"]
            param_sheet["C1"] = "Date"
            param_sheet["C2"] = date(2025, 1, 1)

            builder = ReformExcelBuilder(
                baseline_class=None, path_or_file=to_wb_file(wb)
            )
            assert builder.get_parameters("_2025") == [
                ("parenting_allowance.amount", 100000, date(2025, 1, 1))
            ]

    class TestReformExcel:
        def test_init(self, tax_benefit_system):
            reform = ReformExcel(
                baseline=tax_benefit_system,
                root_name="benefits",
                period="2025-01-01",
                reformed_parameters=[("parenting_allowance.amount", 1000.0, None)],
            )

            assert reform.root_name == "benefits"
            assert reform.period == "2025-01-01"
            assert reform.reformed_parameters == [
                ("parenting_allowance.amount", 1000.0, None)
            ]

            parameter, _ = reform.get_parameter_node(
                reform.parameters, "benefits.parenting_allowance.amount"
            )
            assert parameter.get_at_instant("2025-01-01") == 1000.0

        def test_brackets(self, tax_benefit_system):
            reform = ReformExcel(
                baseline=tax_benefit_system,
                root_name="taxes",
                period="2025-01-01",
                reformed_parameters=[
                    ("social_security_contribution.0", 0.01, None),
                    ("social_security_contribution.3000", 0.03, None),
                    ("social_security_contribution.6000", 0.13, None),
                    ("social_security_contribution.12400", 0.001, None),
                ],
            )
            parameter, _ = reform.get_parameter_node(
                reform.parameters, "taxes.social_security_contribution"
            )
            assert isinstance(parameter, ParameterScale)
            p_instant = parameter.get_at_instant("2025-01")
            assert len(p_instant.rates) == 4
            assert len(p_instant.thresholds) == 4
            assert p_instant.rates == [0.01, 0.03, 0.13, 0.001]
            assert p_instant.thresholds == [0.0, 3000.0, 6000.0, 12400.0]

        def test_unsorted_brackets(self, tax_benefit_system):
            reform = ReformExcel(
                baseline=tax_benefit_system,
                root_name="taxes",
                period="2025-01-01",
                reformed_parameters=[
                    ("social_security_contribution.6000", 0.13, None),
                    ("social_security_contribution.0", 0.01, None),
                    ("social_security_contribution.12400", 0.001, None),
                    ("social_security_contribution.3000", 0.03, None),
                ],
            )
            parameter, _ = reform.get_parameter_node(
                reform.parameters, "taxes.social_security_contribution"
            )
            assert isinstance(parameter, ParameterScale)
            p_instant = parameter.get_at_instant("2025-01")
            assert len(p_instant.rates) == 4
            assert len(p_instant.thresholds) == 4
            assert p_instant.rates == [0.01, 0.03, 0.13, 0.001]
            assert p_instant.thresholds == [0.0, 3000.0, 6000.0, 12400.0]

        def test_parameters_with_date(self, tax_benefit_system):
            reform = ReformExcel(
                baseline=tax_benefit_system,
                root_name="benefits",
                period="2025-01-01",
                reformed_parameters=[
                    ("basic_income", 500.0, None),
                    ("basic_income", 600.0, date(2026, 1, 1)),
                ],
            )

            parameter, _ = reform.get_parameter_node(
                reform.parameters, "benefits.basic_income"
            )
            assert parameter.get_at_instant("2025-06-01") == 500.0
            assert parameter.get_at_instant("2026-06-01") == 600.0

        def test_bracket_parameters_with_date(self, tax_benefit_system):
            reform = ReformExcel(
                baseline=tax_benefit_system,
                root_name="taxes",
                period="2025-01-01",
                reformed_parameters=[
                    ("social_security_contribution.0", 0.02, None),
                    ("social_security_contribution.6000", 0.06, None),
                    ("social_security_contribution.12400", 0.12, None),
                    ("social_security_contribution.0", 0.03, date(2026, 1, 1)),
                    ("social_security_contribution.6000", 0.07, date(2026, 1, 1)),
                    ("social_security_contribution.12400", 0.13, date(2026, 1, 1)),
                ],
            )

            parameter, _ = reform.get_parameter_node(
                reform.parameters, "taxes.social_security_contribution"
            )
            assert isinstance(parameter, ParameterScale)

            p_instant_2025 = parameter.get_at_instant("2025-06")
            assert p_instant_2025.rates == [0.02, 0.06, 0.12]

            p_instant_2026 = parameter.get_at_instant("2026-06")
            assert p_instant_2026.rates == [0.05, 0.13, 0.25]

    class TestReformExcelGenerator:
        def test_generate_parameter_data(self, tax_benefit_system):
            reform = ReformExcel(
                baseline=tax_benefit_system,
                root_name="benefits",
                period="2025-01-01",
            )

            parameters = reform.parameter_data
            assert parameters == [
                ("basic_income", 600.0),
                ("housing_allowance", None),
                ("parenting_allowance.amount", 600.0),
                ("parenting_allowance.income_threshold", 500),
            ]

        def test_generate_parameter_data_with_scale(self, tax_benefit_system):
            reform = ReformExcel(
                baseline=tax_benefit_system,
                root_name="taxes",
                period="2025-01-01",
            )

            io_bytes = io.BytesIO()
            reform.generate_template_xlsx(io_bytes)
            io_bytes.seek(0)
            wb = openpyxl.load_workbook(io_bytes)
            config_sheet = wb["Config"]
            assert config_sheet["A2"].value == "root"
            assert config_sheet["B2"].value == "taxes"
            assert config_sheet["A3"].value == "period"
            assert config_sheet["B3"].value == "2025-01-01"
            param_sheet = wb["Paramètres"]
            rows = list(param_sheet.iter_rows(values_only=True))
            assert rows == [
                ("Nom", "Valeur", "Date"),
                ("housing_tax.minimal_amount", 200, None),
                ("housing_tax.rate", 10, None),
                ("income_tax_rate", 0.15, None),
                ("taxes.social_security_contribution.0.0", 0.02, None),
                ("taxes.social_security_contribution.12400.0", 0.12, None),
                ("taxes.social_security_contribution.6000.0", 0.06, None),
            ]
