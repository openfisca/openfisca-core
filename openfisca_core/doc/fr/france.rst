.. currentmodule:: src.countries.france
.. _france:

****************************
France
****************************	

Paramètres généraux
-------------------

Les entités du modèle socio-fiscal français sont l'individu, le foyer fiscal, la famille (le foyer social) et
le ménage. 

Le modèle socio-fiscal français est décrit dans le paquet :mod:`src.countries.france`.

.. literalinclude:: ../../../src/countries/france/__init__.py  


Description du modèle socio-fiscal
----------------------------------

Les variables nécessaires au calcul de l'ensemble des prestations, ainsi que les entitées auxquelles elles
se rapportent, sont répertoriées dans la classe suivante:

.. automodule:: src.countries.france.model.data
   :members:
   :private-members:
   :show-inheritance:
   
dont voici l'intégralité du code:

.. literalinclude:: ../../../src/countries/france/model/data.py  


Les impôts et les prestations disponibles sont rassemblées dans différents modules.

Les cotisations sociales
~~~~~~~~~~~~~~~~~~~~~~~~

Les cotisations sociales

.. automodule:: src.countries.france.model.cotsoc
   :members: 
   :private-members:

L'impôt sur le revenu
~~~~~~~~~~~~~~~~~~~~~

L'IRPP.

.. automodule:: src.countries.france.model.irpp
   :members: 
   :private-members:
   

Les charges déductibles.

.. automodule:: src.countries.france.model.irpp_charges_deductibles
   :members: 
   :private-members:
   

Les réductions d'impôts.

.. automodule:: src.countries.france.model.irpp_reductions_impots
   :members: 
   :private-members:

Les crédits d'impôts

.. automodule:: src.countries.france.model.irpp_credits_impots
   :members: 
   :private-members:

L'impôt de solidarité sur la fortune et le bouclier fiscal
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automodule:: src.countries.france.model.isf
   :members: 
   :private-members:
   

Les minimas sociaux
~~~~~~~~~~~~~~~~~~~

.. automodule:: src.countries.france.model.mini
   :members: 
   :private-members:

Les allocations familiales
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automodule:: src.countries.france.model.pfam
   :members: 
   :private-members:


Les allocations logement
~~~~~~~~~~~~~~~~~~~~~~~~

.. automodule:: src.countries.france.model.lgtm
   :members: 
   :private-members:
   
La taxe d'habitation
~~~~~~~~~~~~~~~~~~~~

.. automodule:: src.countries.france.model.th
   :members: 
   :private-members:
   
   
D'autres caractéristiques sont également disponibles.

.. automodule:: src.countries.france.model.common
   :members: 
   :private-members:
   
.. automodule:: src.countries.france.model.calage
   :members: 
   :private-members:

   
Avertissement
-------------

OpenFisca calcule le montant de l'impôt sur le revenu et des prestations, 
pour l'année indiquée, à partir des informations que vous avez saisies.
Ces montants sont donnés à titre indicatif et pourront être différents quand ils
seront calculés par l'administration ou la Caf au moment de l'étude de votre dossier.
Les résultats fournis ne sauraient engager l'administration ou votre Caf sur le montant
définitif de l'impôt à acquitter ou des prestations versées. En effet, votre situation 
familiale et/ou vos ressources ou celles de l’un des membres de votre famille peuvent
changer ou ne pas avoir été prises en compte lors de la simulation et certaines hypothèses 
simplificatrices ont été effectuées.
   