import numpy
import os


from openfisca_core.tools import assert_near
from openfisca_core.parameters import ParameterNode
from openfisca_core.model_api import *  # noqa

LOCAL_DIR = os.path.dirname(os.path.abspath(__file__))

parameters = ParameterNode(directory_path = LOCAL_DIR)


def get_message(error):
    return error.args[0]


def test_on_leaf():
    parameter_at_instant = parameters.trimtp_rg('1995-01-01')
    date_de_naissance = numpy.array(['1930-01-01', '1935-01-01', '1940-01-01', '1945-01-01'], dtype = 'datetime64[D]')
    assert_near(parameter_at_instant.nombre_trimestres_cibles_par_generation[date_de_naissance], [150, 152, 157, 160])


def test_on_node():
    date_de_naissance = numpy.array(['1950-01-01', '1953-01-01', '1956-01-01', '1959-01-01'], dtype = 'datetime64[D]')
    parameter_at_instant = parameters.aad_rg('2012-03-01')
    node = parameter_at_instant.age_annulation_decote_en_fonction_date_naissance[date_de_naissance]
    assert_near(node.annee, [65, 66, 67, 67])
    assert_near(node.mois, [0, 2, 0, 0])


# def test_inhomogenous():
#     date_de_naissance = numpy.array(['1930-01-01', '1935-01-01', '1940-01-01', '1945-01-01'], dtype = 'datetime64[D]')
#     parameter_at_instant = parameters.aad_rg('2011-01-01')
#     parameter_at_instant.age_annulation_decote_en_fonction_date_naissance[date_de_naissance]
#     with pytest.raises(ValueError) as error:
#         parameter_at_instant.age_annulation_decote_en_fonction_date_naissance[date_de_naissance]
#     assert "Cannot use fancy indexing on parameter node 'aad_rg.age_annulation_decote_en_fonction_date_naissance'" in get_message(error.value)
