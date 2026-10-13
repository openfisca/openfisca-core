from openfisca_core.entities import build_entity


def test_france_config():
    _Famille = build_entity(
        key="famille",
        plural="familles",
        label="Famille",
        roles=[
            {
                "key": "parent",
                "plural": "parents",
                "label": "Parents",
                "subroles": ["demandeur", "conjoint"],
            },
            {"key": "enfant", "plural": "enfants", "label": "Enfants"},
        ],
    )

    _Individu = build_entity(
        key="individu", plural="individus", label="Individu", is_person=True
    )

    _FoyerFiscal = build_entity(
        key="foyer_fiscal",
        plural="foyers_fiscaux",
        label="Déclaration d’impôts",
        doc="",
        roles=[
            {
                "key": "declarant",
                "plural": "declarants",
                "label": "Déclarants",
                "subroles": ["declarant_principal", "conjoint"],
            },
            {
                "key": "personne_a_charge",
                "plural": "personnes_a_charge",
                "label": "Personnes à charge",
            },
        ],
    )

    _Menage = build_entity(
        key="menage",
        plural="menages",
        label="Logement principal",
        doc="",
        roles=[
            {
                "key": "personne_de_reference",
                "label": "Personne de référence",
                "max": 1,
            },
            {"key": "conjoint", "label": "Conjoint", "max": 1},
            {
                "key": "enfant",
                "plural": "enfants",
                "label": "Enfants",
            },
            {"key": "autre", "plural": "autres", "label": "Autres"},
        ],
    )


def test_country_template_config():
    build_entity.reset_entity_manager()
    _Household = build_entity(
        key="household",
        plural="households",
        label="All the people in a family or group who live together in the same place.",
        doc="",
        roles=[
            {
                "key": "adult",
                "plural": "adults",
                "label": "Adult",
                "doc": "The adults of the household.",
            },
            {
                "key": "child",
                "plural": "children",
                "label": "Child",
                "doc": "The non-adults of the household.",
            },
        ],
    )

    _Person = build_entity(
        key="person",
        plural="persons",
        label="An individual. The minimal entity on which legislation can be applied.",
        doc="",
        is_person=True,
    )
