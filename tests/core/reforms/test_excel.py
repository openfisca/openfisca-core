from tempfile import NamedTemporaryFile

import openpyxl
import pytest

from openfisca_core.parameters.parameter_scale import ParameterScale
from openfisca_core.reforms.reform_excel import ReformExcel, ReformExcelBuilder


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
    def wb_path(self, wb):
        with NamedTemporaryFile(suffix=".xlsx") as fp:
            wb.save(fp.name)
            fp.seek(0)
            yield fp.name

    class TestReformExcelBuilder:
        def test_get_suffixes(self, wb_path):
            builder = ReformExcelBuilder(baseline_class=None, path=wb_path)
            suffixes = builder.get_suffixes()
            assert suffixes == ["", "_2025"]

        def test_get_reform_data(self, wb_path):
            builder = ReformExcelBuilder(baseline_class=None, path=wb_path)
            reform_data = builder.get_reform_data("_2025")

            assert reform_data["root_name"] == "benefits"
            assert reform_data["period"] == "2025-01-01"
            assert reform_data["parameters"] == [("parenting_allowance.amount", 100000)]

        def test_build_reform(self, tax_benefit_system_class, wb_path):
            builder = ReformExcelBuilder(
                baseline_class=tax_benefit_system_class, path=wb_path
            )
            reform = builder.build_reform("_2025")

            assert reform.root_name == "benefits"
            assert reform.period == "2025-01-01"
            assert reform.reformed_parameters == [
                ("parenting_allowance.amount", 100000)
            ]

        def test_pas_de_root(self, tax_benefit_system_class, wb):
            ws = wb["Config"]
            ws.delete_rows(2)

            builder = ReformExcelBuilder(baseline_class=tax_benefit_system_class, wb=wb)
            with pytest.raises(AssertionError):
                builder.build_reform("_2025")

        def test_pas_de_period(self, tax_benefit_system_class, wb):
            ws = wb["Config"]
            ws.delete_rows(3)

            builder = ReformExcelBuilder(baseline_class=tax_benefit_system_class, wb=wb)
            with pytest.raises(AssertionError):
                builder.build_reform("_2025")

    class TestReformExcel:
        def test_init(self, tax_benefit_system):
            reform = ReformExcel(
                baseline=tax_benefit_system,
                root_name="benefits",
                period="2025-01-01",
                reformed_parameters=[("parenting_allowance.amount", 1000.0)],
            )

            assert reform.root_name == "benefits"
            assert reform.period == "2025-01-01"
            assert reform.reformed_parameters == [
                ("parenting_allowance.amount", 1000.0)
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
                    ("social_security_contribution.0", 0.01),
                    ("social_security_contribution.3000", 0.03),
                    ("social_security_contribution.6000", 0.13),
                    ("social_security_contribution.12400", 0.001),
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
                    ("social_security_contribution.6000", 0.13),
                    ("social_security_contribution.0", 0.01),
                    ("social_security_contribution.12400", 0.001),
                    ("social_security_contribution.3000", 0.03),
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

    class TestReformExcelGenerator:
        def test_generate_parameter_data(self, tax_benefit_system):
            reform = ReformExcel(
                baseline=tax_benefit_system,
                root_name="benefits",
                period="2025-01-01",
            )

            parameters = reform.get_parameter_data()
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

            with NamedTemporaryFile(suffix=".xlsx") as fp:
                reform.generate_template_xlsx(fp.name)
                fp.seek(0)
                wb = openpyxl.load_workbook(fp.name)
                config_sheet = wb["Config"]
                assert config_sheet["A2"].value == "root"
                assert config_sheet["B2"].value == "taxes"
                assert config_sheet["A3"].value == "period"
                assert config_sheet["B3"].value == "2025-01-01"
                param_sheet = wb["Paramètres"]
                rows = list(param_sheet.iter_rows(values_only=True))
                assert rows == [
                    ("Nom", "Valeur"),
                    ("housing_tax.minimal_amount", 200),
                    ("housing_tax.rate", 10),
                    ("income_tax_rate", 0.15),
                    ("taxes.social_security_contribution.0.0", 0.02),
                    ("taxes.social_security_contribution.12400.0", 0.12),
                    ("taxes.social_security_contribution.6000.0", 0.06),
                ]
