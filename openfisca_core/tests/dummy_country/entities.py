# -*- coding: utf-8 -*-

from openfisca_core.entities import build_entity

Famille = build_entity(
    key = "famille",
    plural = "familles",
    label = u'Famille',
    roles = [
        {
            'key': 'parent',
            'plural': 'parents',
            'label': u'Parents',
            'subroles': ['demandeur', 'conjoint']
            },
        {
            'key': 'enfant',
            'plural': 'enfants',
            'label': u'Enfants',
            }
        ]
    )


Individu = build_entity(
    key = "individu",
    plural = "individus",
    label = u'Individu',
    is_person = True,
    )

entities = [Individu, Famille]
