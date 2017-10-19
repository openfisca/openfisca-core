===============
openfisca serve
===============

.. argparse::
   :module: openfisca_core.scripts.openfisca_command
   :func: get_parser
   :prog: openfisca
   :path: serve

Additional arguments
--------------------

``openfisca serve`` uses ``gunicorn`` under the hood. In addition to the arguments listed above, you can use any ``gunicorn`` arguments when running ``openfisca serve`` (e.g. ``--reload``, ``--workers``, ``--timeout``).

Examples
--------

Basic use
^^^^^^^^^

.. code-block:: shell

  openfisca serve --country_package openfisca_france


Serving extensions
^^^^^^^^^^^^^^^^^^

.. code-block:: shell

  openfisca serve --country_package openfisca_france --extensions openfisca_paris


Serving reforms
^^^^^^^^^^^^^^^

.. code-block:: shell

  openfisca serve --country_package openfisca_france --reforms openfisca_france.reforms.plf2015.plf2015


Using a configuration file
^^^^^^^^^^^^^^^^^^^^^^^^^^

**config.py:**

.. code-block:: py

  port = 4000
  workers = 4
  country_package = 'openfisca_france'
  extensions = ['openfisca_paris']

**Command line:**

.. code-block:: shell

  openfisca serve --configuration-file config.py



