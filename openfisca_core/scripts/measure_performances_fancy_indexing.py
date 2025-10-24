# flake8: noqa T001

import timeit

import numpy
from openfisca_france import CountryTaxBenefitSystem

tbs = CountryTaxBenefitSystem()
N = 200000
al_plaf_acc = tbs.get_parameters_at_instant("2015-01-01").prestations.al_plaf_acc
zone_apl = numpy.random.choice([1, 2, 3], N)
al_nb_pac = numpy.random.choice(6, N)
couple = numpy.random.choice([True, False], N)
formatted_zone = concat(
    "plafond_pour_accession_a_la_propriete_zone_",
    zone_apl,
)  # zone_apl returns 1, 2 or 3 but the parameters have a long name


def formula_with():
    plafonds = al_plaf_acc[formatted_zone]

    return (
        plafonds.personne_isolee_sans_enfant * not_(couple) * (al_nb_pac == 0)
        + plafonds.menage_seul * couple * (al_nb_pac == 0)
        + plafonds.menage_ou_isole_avec_1_enfant * (al_nb_pac == 1)
        + plafonds.menage_ou_isole_avec_2_enfants * (al_nb_pac == 2)
        + plafonds.menage_ou_isole_avec_3_enfants * (al_nb_pac == 3)
        + plafonds.menage_ou_isole_avec_4_enfants * (al_nb_pac == 4)
        + plafonds.menage_ou_isole_avec_5_enfants * (al_nb_pac >= 5)
        + plafonds.menage_ou_isole_par_enfant_en_plus
        * (al_nb_pac > 5)
        * (al_nb_pac - 5)
    )


def formula_without():
    z1 = al_plaf_acc.plafond_pour_accession_a_la_propriete_zone_1
    z2 = al_plaf_acc.plafond_pour_accession_a_la_propriete_zone_2
    z3 = al_plaf_acc.plafond_pour_accession_a_la_propriete_zone_3

    return (
        (zone_apl == 1)
        * (
            z1.personne_isolee_sans_enfant * not_(couple) * (al_nb_pac == 0)
            + z1.menage_seul * couple * (al_nb_pac == 0)
            + z1.menage_ou_isole_avec_1_enfant * (al_nb_pac == 1)
            + z1.menage_ou_isole_avec_2_enfants * (al_nb_pac == 2)
            + z1.menage_ou_isole_avec_3_enfants * (al_nb_pac == 3)
            + z1.menage_ou_isole_avec_4_enfants * (al_nb_pac == 4)
            + z1.menage_ou_isole_avec_5_enfants * (al_nb_pac >= 5)
            + z1.menage_ou_isole_par_enfant_en_plus * (al_nb_pac > 5) * (al_nb_pac - 5)
        )
        + (zone_apl == 2)
        * (
            z2.personne_isolee_sans_enfant * not_(couple) * (al_nb_pac == 0)
            + z2.menage_seul * couple * (al_nb_pac == 0)
            + z2.menage_ou_isole_avec_1_enfant * (al_nb_pac == 1)
            + z2.menage_ou_isole_avec_2_enfants * (al_nb_pac == 2)
            + z2.menage_ou_isole_avec_3_enfants * (al_nb_pac == 3)
            + z2.menage_ou_isole_avec_4_enfants * (al_nb_pac == 4)
            + z2.menage_ou_isole_avec_5_enfants * (al_nb_pac >= 5)
            + z2.menage_ou_isole_par_enfant_en_plus * (al_nb_pac > 5) * (al_nb_pac - 5)
        )
        + (zone_apl == 3)
        * (
            z3.personne_isolee_sans_enfant * not_(couple) * (al_nb_pac == 0)
            + z3.menage_seul * couple * (al_nb_pac == 0)
            + z3.menage_ou_isole_avec_1_enfant * (al_nb_pac == 1)
            + z3.menage_ou_isole_avec_2_enfants * (al_nb_pac == 2)
            + z3.menage_ou_isole_avec_3_enfants * (al_nb_pac == 3)
            + z3.menage_ou_isole_avec_4_enfants * (al_nb_pac == 4)
            + z3.menage_ou_isole_avec_5_enfants * (al_nb_pac >= 5)
            + z3.menage_ou_isole_par_enfant_en_plus * (al_nb_pac > 5) * (al_nb_pac - 5)
        )
    )


if __name__ == "__main__":
    time_with = timeit.timeit(
        "formula_with()",
        setup="from __main__ import formula_with",
        number=50,
    )
    time_without = timeit.timeit(
        "formula_without()",
        setup="from __main__ import formula_without",
        number=50,
    )
