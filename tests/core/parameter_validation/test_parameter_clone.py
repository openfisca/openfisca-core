import os

from openfisca_core.parameters import ParameterNode

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
year = 2016


def test_clone():
    path = os.path.join(BASE_DIR, 'filesystem_hierarchy')
    parameters = ParameterNode('', directory_path = path)
    parameters_at_instant = parameters('2016-01-01')
    assert parameters_at_instant.node1.param == 1.0
    clone = parameters.clone()
    clone_at_instant = clone('2016-01-01')
    assert clone_at_instant.node1.param == 1.0
    assert id(clone) != id(parameters)
    assert id(clone.node1) != id(parameters.node1)
    assert id(clone.node1.param) != id(parameters.node1.param)


def test_clone_parameter(tax_benefit_system):

    param = tax_benefit_system.parameters.taxes.income_tax_rate
    clone = param.clone()

    assert clone is not param
    assert clone.values_list is not param.values_list
    assert clone.values_list[0] is not param.values_list[0]

    assert clone.values_list == param.values_list


def test_clone_parameter_node(tax_benefit_system):
    node = tax_benefit_system.parameters.taxes
    clone = node.clone()

    assert clone is not node
    assert clone.income_tax_rate is not node.income_tax_rate
    assert clone.children['income_tax_rate'] is not node.children['income_tax_rate']


def test_clone_scale(tax_benefit_system):
    scale = tax_benefit_system.parameters.taxes.social_security_contribution
    clone = scale.clone()

    assert clone.brackets[0] is not scale.brackets[0]
    assert clone.brackets[0].rate is not scale.brackets[0].rate


def test_deep_edit(tax_benefit_system):
    parameters = tax_benefit_system.parameters
    clone = parameters.clone()

    param = parameters.taxes.income_tax_rate
    clone_param = clone.taxes.income_tax_rate

    original_value = param.values_list[0].value
    clone_param.values_list[0].value = 100
    assert param.values_list[0].value == original_value

    scale = parameters.taxes.social_security_contribution
    clone_scale = clone.taxes.social_security_contribution

    original_scale_value = scale.brackets[0].rate.values_list[0].value
    clone_scale.brackets[0].rate.values_list[0].value = 10

    assert scale.brackets[0].rate.values_list[0].value == original_scale_value
