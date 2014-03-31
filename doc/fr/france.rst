.. currentmodule:: openfisca_france
.. _france:

****************************
France
****************************	

Paramètres généraux
-------------------

Les entités du modèle socio-fiscal français sont l'individu, le foyer fiscal, la famille (le foyer social) et
le ménage.

Le modèle socio-fiscal français est décrit dans le paquet :mod:`openfisca_france`.

.. literalinclude:: ../../../src/countries/france/__init__.py


Description du modèle socio-fiscal
----------------------------------

Les variables nécessaires au calcul de l'ensemble des prestations, ainsi que les entitées auxquelles elles
se rapportent, sont répertoriées dans la classe suivante:

.. automodule:: openfisca_france.model.data
   :members:
   :private-members:
   :show-inheritance:

dont voici l'intégralité du code:

.. literalinclude:: ../../../src/countries/france/model/data.py


Les impôts et les prestations disponibles sont rassemblées dans différents modules.

Les cotisations sociales
~~~~~~~~~~~~~~~~~~~~~~~~

Les cotisations sociales

.. automodule:: openfisca_france.model.cotsoc
   :members:
   :private-members:

L'impôt sur le revenu
~~~~~~~~~~~~~~~~~~~~~

L'IRPP.

.. automodule:: openfisca_france.model.irpp
   :members:
   :private-members:


Les charges déductibles.

.. automodule:: openfisca_france.model.irpp_charges_deductibles
   :members:
   :private-members:


Les réductions d'impôts.

.. automodule:: openfisca_france.model.irpp_reductions_impots
   :members:
   :private-members:

Les crédits d'impôts

.. automodule:: openfisca_france.model.irpp_credits_impots
   :members:
   :private-members:

L'impôt de solidarité sur la fortune et le bouclier fiscal
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automodule:: openfisca_france.model.isf
   :members:
   :private-members:


Les minimas sociaux
~~~~~~~~~~~~~~~~~~~

.. automodule:: openfisca_france.model.mini
   :members:
   :private-members:

Les allocations familiales
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automodule:: openfisca_france.model.pfam
   :members:
   :private-members:


Les allocations logement
~~~~~~~~~~~~~~~~~~~~~~~~

.. automodule:: openfisca_france.model.lgtm
   :members:
   :private-members:

La taxe d'habitation
~~~~~~~~~~~~~~~~~~~~

.. automodule:: openfisca_france.model.th
   :members:
   :private-members:


D'autres caractéristiques sont également disponibles.

.. automodule:: openfisca_france.model.common
   :members:
   :private-members:

.. automodule:: openfisca_france.model.calage
   :members:
   :private-members:


Avertissement
-------------

OpenFisca calcule les cotisations et contribution sociales, le montant
de l'impôt sur le revenu et des prestations sociales, pour l'année
indiquée, à partir des informations que vous avez saisies.  Ces
montants sont donnés à titre indicatif et pourront être différents
de ceux calculés par l'administration ou la Caf au moment de
l'étude de votre dossier.  Les résultats fournis ne sauraient engager
l'administration, votre Caf ou plus généralement n'importe quel
organisme préléveur ou verseur sur le montant définitif des impôts ou
cotisattions à acquitter ou des prestations versées. En effet, votre
situation familiale et/ou vos ressources ou celles de l’un des membres
de votre famille peuvent changer ou ne pas avoir été prises en compte
lors de la simulation et certaines hypothèses simplificatrices ont été
effectuées.
   
