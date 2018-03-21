
![Logo](https://rkuska.fedorapeople.org/pyp2rpm_large.png)

pyp2rpm
=======

A tool to convert a PyPI package to an RPM SPECFILE or to generate an SRPM.
Under heavy development, see the TODO file for a list of planned features.
pyp2rpm currently ships with Fedora and Mageia specific templates.

## Usage

The simplest use case is to run:

    pyp2rpm package_name

This downloads the package from PyPI and outputs the RPM SPECFILE.

Or:

    pyp2rpm package_name --srpm

This downloads the package from PyPI and creates a SRPM file.

All of the options are (print this by running pyp2rpm -h):

    usage: pyp2rpm [-h] [-v VERSION] [-d SAVE_DIR] [-r RPM_NAME]
                   [-t TEMPLATE] [-o DISTRO] [-b BASE_PYTHON]
                   [-p PYTHON_VERSION] [--srpm] [--proxy PROXY] PACKAGE

    Convert PyPI package to RPM specfile or SRPM.

    Arguments:
      PACKAGE             Provide PyPI name of the package or path to compressed
                          source file.

    Options:
      -t TEMPLATE                     Template file (jinja2 format) to render
                                      (default: "fedora").Search order is 1)
                                      filesystem, 2) default templates.
      -o [fedora|epel7|epel6|mageia|pld]
                                      Default distro whose conversion rules to use
                                      (default:"fedora"). Default templates have
                                      their rules associated and ignore this.
      -b BASE_PYTHON                  Base Python version to package for (fedora
                                      default: "3").
      -p PYTHON_VERSIONS              Additional Python versions to include in the
                                      specfile (e.g -p2 for python2 subpackage).
                                      Can be specified multiple times. Specify
                                      additional version or use -b explicitly to
                                      disable default.
      -s                              Spec file ~/rpmbuild/SPECS/python-package_name.spec
                                      will be created (default:
                                      prints spec file to stdout).
      --srpm                          When used pyp2rpm will produce srpm instead
                                      of printing specfile into stdout.
      --proxy PROXY                   Specify proxy in the form proxy.server:port.
      -r RPM_NAME                     Name of rpm package (overrides calculated
                                      name).
      -d SAVE_PATH                    Specify where to save package file, specfile
                                      and generated SRPM (default:
                                      "/home/mcyprian/rpmbuild").
      -v VERSION                      Version of the package to download (ignored
                                      for local files).
      --venv / --no-venv              Enable / disable metadata extraction from
                                      virtualenv (default: enabled).
      --autonc / --no-autonc          Enable / disable using automatic provides
                                      with a standardized name in dependencies
                                      declaration (default: disabled).
      --sclize                        Convert tags and macro definitions to SCL-style
                                      using `spec2scl` module. NOTE: SCL
                                      related options can be provided alongside
                                      this option.
      -h, --help                      Show this message and exit.

    SCL related options:
      --no-meta-runtime-dep       Don't add the runtime dependency on the scl
                                  runtime package.
      --no-meta-buildtime-dep     Don't add the buildtime dependency on the scl
                                  runtime package.
      --skip-functions FUNCTIONS  Comma separated list of transformer functions to
                                  skip.
      --no-deps-convert           Don't convert dependency tags (mutually
                                  exclusive with --list-file).
      --list-file FILE_NAME       List of the packages/provides, that will be in
                                  the SCL (to convert Requires/BuildRequires
                                  properly). Lines in the file are in form of
                                  "pkg-name %%{?custom_prefix}", where the prefix
                                  part is optional.


To run the unit tests, cd into the checked out directory and run:

    PYTHONPATH=$(pwd) py.test

or run:

    python setup.py test


## Example usage

![alt tag](https://mcyprian.fedorapeople.org/pyp2rpm_guide.gif
"Record of pyp2rpm usage")

## Contributing

We will gladly accept any pull request or feature request.
With complex pull requests, please include unit tests in *pytest* and use *flexmock* if you need mocking.

pyp2rpm is licensed under the MIT/Expat license.
