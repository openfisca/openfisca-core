from openfisca_web_api.loader.entities import build_entities
from openfisca_web_api.loader.parameters import build_parameters
from openfisca_web_api.loader.spec import build_openAPI_specification
from openfisca_web_api.loader.variables import build_variables


def build_data(tax_benefit_system):
    country_package_metadata = tax_benefit_system.get_package_metadata()
    parameters = build_parameters(tax_benefit_system, country_package_metadata)
    variables = build_variables(tax_benefit_system, country_package_metadata)
    entities = build_entities(tax_benefit_system)
    data = {
        "tax_benefit_system": tax_benefit_system,
        "country_package_metadata": country_package_metadata,
        "openAPI_spec": None,
        "parameters": parameters,
        "variables": variables,
        "entities": entities,
    }
    data["openAPI_spec"] = build_openAPI_specification(data)

    return data
