.. currentmodule:: src.countries.france
.. _france:



****************************
France
****************************	

Les entités du modèle socio-fiscal français sont l'individu, le foyer fiscal, la famille (le foyer social) et
le ménage. 

Le modèle socio-fiscal français est décrit dans le paquet (package) france.
Les variables nécessaires au calcul de l'ensemble des prestations, ainsi que les entitées auxquelles elles
se rapportent, sont répertoriées dans la classe suivante:

.. automodule:: src.countries.france.model.data
   :members: 
   :private-members:

dont voici l'intégralité du code:

.. literalinclude:: ../src/countries/france/model/data.py  


Les impôts et les prestations disponibles sont rassemblées dans différents modules.

Les cotisations sociales
------------------------

.. automodule:: src.countries.france.model.cotsoc
   :members: 
   :private-members:

L'impôt sur le revenu
---------------------

.. automodule:: src.countries.france.model.irpp
   :members: 
   :private-members:

.. automodule:: src.countries.france.model.irpp_charges_deductibles
   :members: 
   :private-members:
   
.. automodule:: src.countries.france.model.irpp_reductions_impots
   :members: 
   :private-members:

.. automodule:: src.countries.france.model.irpp_credits_impots
   :members: 
   :private-members:

L'impôt de solidarité sur la fortune et le bouclier fiscal
----------------------------------------------------------

.. automodule:: src.countries.france.model.isf
   :members: 
   :private-members:
   

Les minimas sociaux
-------------------

.. automodule:: src.countries.france.model.mini
   :members: 
   :private-members:

Les allocations familiales
--------------------------

.. automodule:: src.countries.france.model.pfam
   :members: 
   :private-members:


Les allocations logement
------------------------

.. automodule:: src.countries.france.model.lgtm
   :members: 
   :private-members:
   
La taxe d'habitation
--------------------

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
