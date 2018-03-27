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

``openfisca serve`` uses ``gunicorn`` under the hood. In addition to the arguments listed above, you can use any ``gunicorn`` arguments when running ``openfisca serve`` (e.g. ``--reload``, ``--workers``, ``--timeout``, ``--bind``).
See:

.. code-block:: shell

  gunicorn --help


Examples
--------

Basic use
^^^^^^^^^

.. code-block:: shell

  openfisca serve --country-package openfisca_france


Serving extensions
^^^^^^^^^^^^^^^^^^

.. code-block:: shell

  openfisca serve --country-package openfisca_france --extensions openfisca_paris


Serving reforms
^^^^^^^^^^^^^^^

.. code-block:: shell

  openfisca serve --country-package openfisca_france --reforms openfisca_france.reforms.plf2015.plf2015


Using a configuration file
^^^^^^^^^^^^^^^^^^^^^^^^^^
You can setup ``openfisca serve`` using a configuration file. Be careful as parameters with a '-' in their name on command line change to an '_' when used from the config file. See this example of configuration:

**config.py:**

.. code-block:: py

  port = 4000
  workers = 4
  bind = '0.0.0.0:{}'.format(port)
  country_package = 'openfisca_france'
  extensions = ['openfisca_paris']

**Command line:**

.. code-block:: shell

  openfisca serve --configuration-file config.py
