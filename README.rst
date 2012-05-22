=======
pyp2rpm
=======
Tool to convert a package from PyPI to RPM SPECFILE.
Under heavy development, see TODO file for list of planned features.

Usage:

The most simple use case is running::

    pyp2rpm -n package_name

This downloads the package from PyPI and outputs the RPM SPECFILE.

All of the options are (print this by running pyp2rpm -h::

    usage: pyp2rpm [-h] -n PYPI_NAME [-v VERSION] [-m METADATA_SOURCE]
                   [-s PACKAGE_SOURCE] [-d SAVE_DIR] [-t TEMPLATE]

    Convert PyPI package to RPM specfile.

    optional arguments:
    -h, --help          show this help message and exit
    -n PYPI_NAME        Name of the package on PyPI (ignored for local files).
    -v VERSION          Version of the package to download (ignored for local files).
    -m METADATA_SOURCE  Where to get metadata from ("pypi" or "local", default: "pypi").
    -s PACKAGE_SOURCE   Where to get package from ("pypi" or "/full/path/to/local/file", default: "pypi").
    -d SAVE_DIR         Where to save the package file (default: "/home/bkabrda/rpmbuild/SOURCES/")
    -t TEMPLATE         Template file (jinja2 format) to render (default: "fedora"). Search order is 1) filesystem, 2) default templates.
    -p PYTHON_VERSION   Additional Python versions to include in the specfile (e.g -p3 for %{?with_python3}). Can be specified multiple times.


To run the unit tests, cd into the checked out directory and run::

    PYTHONPATH=$(pwd) py.test

I will gladly accept any pull request or recommendation.
With complex pull requests, please include unit tests in *pytest*, use *flexmock* if you need mocking.

pyp2rpm is licensed under MIT license.
