.. _install:

************
Installation
************

You have the option to install an `official release
<https://github.com/openfisca/openfisca/downloads>`__
or to build the `development version
<http://github.com/pydata/pandas>`__.


Python version support
~~~~~~~~~~~~~~~~~~~~~~

Officially Python 2.7.


Binary installers
~~~~~~~~~~~~~~~~~

.. _all-platforms:

All platforms
_____________


Preliminary builds and installers on the `OpenFisca download page <https://github.com/openfisca/openfisca/downloads>`__.


Dependencies
~~~~~~~~~~~~

  * `NumPy <http://www.numpy.org>`__: 1.6.1 or higher
  * `python-dateutil <http://labix.org/python-dateutil>`__ 1.5

  * `matplotlib <http://matplotlib.sourceforge.net/>`__: for plotting



TODO: complete this list

.. _install.recommended_dependencies:

  * `PyTables <http://www.pytables.org>`__: necessary for HDF5-based storage
  * `openpyxl <http://packages.python.org/openpyxl/>`__, `xlrd/xlwt <http://www.python-excel.org/>`__
     * openpyxl version 1.6.1 or higher
     * Needed for Excel I/O


.. note::

   Without the optional dependencies, many useful features will not
   work. Hence, it is highly recommended that you install these.

Installing from source
~~~~~~~~~~~~~~~~~~~~~~


The source code is hosted at http://github.com/openfisca/openfisca, it can be checked
out using git and compiled / installed like so:

::

  git clone git://github.com/openfisca/openfisca.git
  cd src
  TODO:


Some informations are available on the `OpenFisca website <http://www.openfisca.fr>`_.


