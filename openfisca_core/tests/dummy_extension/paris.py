from openfisca_core.columns import FloatCol
from openfisca_core.variables import Variable

from openfisca_core.tests.dummy_country.entities import Famille


class paris_logement_familles(Variable):
    column = FloatCol
    label = u"Allocation Paris Logement Famille"
    entity = Famille
