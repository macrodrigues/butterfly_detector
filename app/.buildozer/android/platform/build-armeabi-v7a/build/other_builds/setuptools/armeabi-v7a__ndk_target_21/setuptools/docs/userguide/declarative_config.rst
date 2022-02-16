.. _declarative config:

-----------------------------------------
Configuring setup() using setup.cfg files
-----------------------------------------

.. note:: New in 30.3.0 (8 Dec 2016).

.. important::
    If compatibility with legacy builds (i.e. those not using the :pep:`517`
    build API) is desired, a ``setup.py`` file containing a ``setup()`` function
    call is still required even if your configuration resides in ``setup.cfg``.

``Setuptools`` allows using configuration files (usually :file:`setup.cfg`)
to define a package’s metadata and other options that are normally supplied
to the ``setup()`` function (declarative config).

This approach not only allows automation scenarios but also reduces
boilerplate code in some cases.

.. note::

    This implementation has limited compatibility with the distutils2-like
    ``setup.cfg`` sections used by the ``pbr`` and ``d2to1`` packages.

    Namely: only metadata-related keys from ``metadata`` section are supported
    (except for ``description-file``); keys from ``files``, ``entry_points``
    and ``backwards_compat`` are not supported.


.. code-block:: ini

    [metadata]
    name = my_package
    version = attr: src.VERSION
    description = My package description
    long_description = file: README.rst, CHANGELOG.rst, LICENSE.rst
    keywords = one, two
    license = BSD 3-Clause License
    classifiers =
        Framework :: Django
        License :: OSI Approved :: BSD License
        Programming Language :: Python :: 3
        Programming Language :: Python :: 3.5

    [options]
    zip_safe = False
    include_package_data = True
    packages = find:
    scripts =
        bin/first.py
        bin/second.py
    install_requires =
        requests
        importlib; python_version == "2.6"

    [options.package_data]
    * = *.txt, *.rst
    hello = *.msg

    [options.extras_require]
    pdf = ReportLab>=1.2; RXP
    rest = docutils>=0.3; pack ==1.1, ==1.3

    [options.packages.find]
    exclude =
        src.subpackage1
        src.subpackage2

    [options.data_files]
    /etc/my_package =
        site.d/00_default.conf
        host.d/00_default.conf
    data = data/img/logo.png, data/svg/icon.svg

Metadata and options are set in the config sections of the same name.

* Keys are the same as the keyword arguments one provides to the ``setup()``
  function.

* Complex values can be written comma-separated or placed one per line
  in *dangling* config values. The following are equivalent:

  .. code-block:: ini

      [metadata]
      keywords = one, two

      [metadata]
      keywords =
          one
          two

* In some cases, complex values can be provided in dedicated subsections for
  clarity.

* Some keys allow ``file:``, ``attr:``, ``find:``, and ``find_namespace:`` directives in
  order to cover common usecases.

* Unknown keys are ignored.


Using a ``src/`` layout
=======================

One commonly used package configuration has all the module source code in a
subdirectory (often called the ``src/`` layout), like this::

    ├── src
    │   └── mypackage
    │       ├── __init__.py
    │       └── mod1.py
    ├── setup.py
    └── setup.cfg

You can set up your ``setup.cfg`` to automatically find all your packages in
the subdirectory like this:

.. code-block:: ini

    # This example contains just the necessary options for a src-layout, set up
    # the rest of the file as described above.

    [options]
    package_dir=
        =src
    packages=find:

    [options.packages.find]
    where=src

Specifying values
=================

Some values are treated as simple strings, some allow more logic.

Type names used below:

* ``str`` - simple string
* ``list-comma`` - dangling list or string of comma-separated values
* ``list-semi`` - dangling list or string of semicolon-separated values
* ``bool`` - ``True`` is 1, yes, true
* ``dict`` - list-comma where keys are separated from values by ``=``
* ``section`` - values are read from a dedicated (sub)section


Special directives:

* ``attr:`` - Value is read from a module attribute.  ``attr:`` supports
  callables and iterables; unsupported types are cast using ``str()``.

  In order to support the common case of a literal value assigned to a variable
  in a module containing (directly or indirectly) third-party imports,
  ``attr:`` first tries to read the value from the module by examining the
  module's AST.  If that fails, ``attr:`` falls back to importing the module.

* ``file:`` - Value is read from a list of files and then concatenated


.. note::
    The ``file:`` directive is sandboxed and won't reach anything outside
    the directory containing ``setup.py``.


Metadata
--------

.. note::
    The aliases given below are supported for compatibility reasons,
    but their use is not advised.

==============================  =================  =================  =============== =====
Key                             Aliases            Type               Minimum Version Notes
==============================  =================  =================  =============== =====
name                                               str
version                                            attr:, file:, str  39.2.0          (1)
url                             home-page          str
download_url                    download-url       str
project_urls                                       dict               38.3.0
author                                             str
author_email                    author-email       str
maintainer                                         str
maintainer_email                maintainer-email   str
classifiers                     classifier         file:, list-comma
license                                            str
license_file                                       str
license_files                                      list-comma
description                     summary            file:, str
long_description                long-description   file:, str
long_description_content_type                      str                38.6.0
keywords                                           list-comma
platforms                       platform           list-comma
provides                                           list-comma
requires                                           list-comma
obsoletes                                          list-comma
==============================  =================  =================  =============== =====

.. note::
    A version loaded using the ``file:`` directive must comply with PEP 440.
    It is easy to accidentally put something other than a valid version
    string in such a file, so validation is stricter in this case.

Notes:
1. The ``version`` file attribute has only been supported since 39.2.0.

Options
-------

=======================  ===================================  =============== =====
Key                      Type                                 Minimum Version Notes
=======================  ===================================  =============== =====
zip_safe                 bool
setup_requires           list-semi
install_requires         list-semi
extras_require           section
python_requires          str
entry_points             file:, section
use_2to3                 bool
use_2to3_fixers          list-comma
use_2to3_exclude_fixers  list-comma
convert_2to3_doctests    list-comma
scripts                  list-comma
eager_resources          list-comma
dependency_links         list-comma
tests_require            list-semi
include_package_data     bool
packages                 find:, find_namespace:, list-comma
package_dir              dict
package_data             section                                              (1)
exclude_package_data     section
namespace_packages       list-comma
py_modules               list-comma
data_files               dict                                 40.6.0
=======================  ===================================  =============== =====

.. note::

    **packages** - The ``find:`` and ``find_namespace:`` directive can be further configured
    in a dedicated subsection ``options.packages.find``. This subsection
    accepts the same keys as the ``setuptools.find_packages`` and the
    ``setuptools.find_namespace_packages`` function:
    ``where``, ``include``, and ``exclude``.

    **find_namespace directive** - The ``find_namespace:`` directive is supported since Python >=3.3.

Notes:
1. In the ``package_data`` section, a key named with a single asterisk (``*``)
refers to all packages, in lieu of the empty string used in ``setup.py``.
