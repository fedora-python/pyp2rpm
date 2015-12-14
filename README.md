
![Logo](https://rkuska.fedorapeople.org/pyp2rpm_large.png)  

=======
pyp2rpm
=======

Tool to convert a package from PyPI to RPM SPECFILE or to generate SRPM.
Under heavy development, see TODO file for list of planned features.
pyp2rpm currently ships with Fedora and Mageia specific templates.

## Usage

The simplest use case is running:

    pyp2rpm package_name

This downloads the package from PyPI and outputs the RPM SPECFILE.

Or:

    pyp2rpm package_name --srpm

This downloads the package from PyPI and creates SRPM file.

All of the options are (print this by running pyp2rpm -h):

    usage: pyp2rpm [-h] [-v VERSION] [-d SAVE_DIR] [-r RPM_NAME] 
                   [-t TEMPLATE] [-o DISTRO] [-b BASE_PYTHON] 
                   [-p PYTHON_VERSION] [--srpm] [--proxy PROXY] PACKAGE

    Convert PyPI package to RPM specfile or SRPM.

    arguments:
      PACKAGE             Provide PyPI name of the package or path to compressed 
                          source file.

    optional arguments:
      -h, --help          show this help message and exit
      -v VERSION          Version of the package to download (ignored for local files).
      -d SAVE_DIR         Where to save the package file (default: "~/rpmbuild")
      -r RPM_NAME         Name of rpm package (overrides calculated name)
      -t TEMPLATE         Template file (jinja2 format) to render (default: "fedora"). 
                          Search order is 1) filesystem, 2) default templates.
      -o DISTRO           Default distro whose conversion rules to use 
                          (default: "fedora"). Default templates have their rules 
                          associated and ignore this.
      -b BASE_PYTHON      Base Python version to package for (default: "2").
      -p PYTHON_VERSIONS  Additional Python versions to include in the specfile 
                          (e.g -p3 for %{?with_python3}). Can be specified multiple times
                          (default: "3"). Specify additional version or use -b
                          explicitly to disable default. 
      --srpm              When used pyp2rpm will produce srpm instead of printing 
                          specfile into stdout.
      --proxy PROXY       Specify proxy in the form proxy.server:port.
      --venv / --no-venv  Enable / disable metadata extraction from virtualenv



To run the unit tests, cd into the checked out directory and run:

    PYTHONPATH=$(pwd) py.test

or run:

    python setup.py test


## Example usage

![alt tag](https://mcyprian.fedorapeople.org/pyp2rpm_guide.gif 
"Record of pyp2rpm usage")

## Contributing

We will gladly accept any pull request or recommendation.
With complex pull requests, please include unit tests in *pytest*, use *flexmock* if you need mocking.

pyp2rpm is licensed under MIT license.
