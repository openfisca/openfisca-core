# -*- coding: utf-8 -*-

from openfisca_core import conv
from openfisca_core.scenarios import AbstractScenario


class Scenario(AbstractScenario):
    def init_single_entity(self, axes = None, enfants = None, famille = None, parent1 = None, parent2 = None,
            period = None):
        if enfants is None:
            enfants = []
        assert parent1 is not None
        famille = famille.copy() if famille is not None else {}
        individus = []
        for index, individu in enumerate([parent1, parent2] + (enfants or [])):
            if individu is None:
                continue
            id = individu.get('id')
            if id is None:
                individu = individu.copy()
                individu['id'] = id = 'ind{}'.format(index)
            individus.append(individu)
            if index <= 1:
                famille.setdefault('parents', []).append(id)
            else:
                famille.setdefault('enfants', []).append(id)
        conv.check(self.make_json_or_python_to_attributes())(dict(
            axes = axes,
            period = period,
            test_case = dict(
                familles = [famille],
                individus = individus,
                ),
            ))
        return self
