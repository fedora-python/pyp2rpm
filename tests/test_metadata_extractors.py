import os

import setuptools
import pytest

from flexmock import flexmock

import pyp2rpm.metadata_extractors as me
from pyp2rpm.name_convertor import NameConvertor
from pyp2rpm import utils

tests_dir = os.path.split(os.path.abspath(__file__))[0]


class TestMetadataExtractor(object):
    td_dir = '{0}/test_data/'.format(tests_dir)

    def setup_method(self, method):
        # create fresh extractors for every test

        self.nc = NameConvertor('fedora')
        self.e = [me.SetupPyMetadataExtractor('{0}plumbum-0.9.0.tar.gz'.format(
            self.td_dir), 'plumbum', self.nc, '0.9.0'),
            me.SetupPyMetadataExtractor(
            '{0}pytest-2.2.3.zip'.format(self.td_dir), 'pytest',
                self.nc, '2.2.3'),
            me.SetupPyMetadataExtractor(
            '{0}bitarray-0.8.0.tar.gz'.format(self.td_dir), 'bitarray',
                self.nc, '0.8.0'),
            me.SetupPyMetadataExtractor(
            '{0}versiontools-1.9.1.tar.gz'.format(self.td_dir),
                'versiontools', self.nc, '1.9.1'),
            me.SetupPyMetadataExtractor(
            '{0}isholiday-0.1.tar.gz'.format(self.td_dir),
                'isholiday', self.nc, '0.1'),
        ]

    @pytest.mark.parametrize(('b_version', 'what', 'expected'), [
        ('2', 'install_requires', ['jinja2', 'jsonschema', 'six',
                                   'py2-ipaddress']),
        ('3', 'install_requires', ['jinja2', 'jsonschema', 'six']),
    ])
    def test_init_extractor(self, b_version, what, expected):
        extractor = me.SetupPyMetadataExtractor(
            '{0}netjsonconfig-0.5.1.tar.gz'.format(self.td_dir),
            'netjsonconfig', self.nc, '0.5.1', base_python_version=b_version)
        if extractor.unsupported_version != b_version:
            assert extractor.metadata.get(what) == expected

    @pytest.mark.parametrize(('lst', 'expected'), [
        ([['Requires', 'pyfoo', 'spam', 'spam']],
         [['Requires', 'python-pyfoo', 'spam', 'spam']]),
        ([['Requires', 'foo', 'spam', 'spam']],
         [['Requires', 'python-foo', 'spam', 'spam']]),
        ([['Requires', 'foo-python']], [['Requires', 'python-foo']]),
        ([['Requires', 'python-foo', 'spam']],
         [['Requires', 'python-foo', 'spam']]),
    ])
    def test_name_convert_deps_list(self, lst, expected):
        assert self.e[0].name_convert_deps_list(lst) == expected

    @pytest.mark.parametrize(('i', 'expected'), [
        (0, True),
        (2, False),
    ])
    def test_has_bundled_egg_info(self, i, expected):
        with self.e[i].archive:
            assert self.e[i].has_bundled_egg_info == expected

    @pytest.mark.parametrize(('i', 'expected'), [
        (0, False),
        (1, False),
        (2, True),
    ])
    def test_has_extension(self, i, expected):
        with self.e[i].archive:
            assert self.e[i].has_extension == expected

    @pytest.mark.parametrize(('i', 'expected'), [
        (0, ['README.rst', 'LICENSE']),
    ])
    def test_doc_files(self, i, expected):
        with self.e[i].archive:
            assert self.e[i].doc_files == expected

    @pytest.mark.parametrize(('i', 'expected'), [
        (0, None),
        (3, 'versiontools-1.9.1/doc'),
    ])
    def test_sphinx_dir(self, i, expected):
        with self.e[i].archive:
            assert self.e[i].sphinx_dir == expected

    @pytest.mark.parametrize(('i', 'expected'), [
        (0, ['2', '3']),
        (2, ['2', '3']),
        (3, ['2', '3']),
        (4, []),
    ])
    def test_extract_versions(self, i, expected):
        if i != 4 or utils.PY3:
            with self.e[i].archive:
                pkgdata = self.e[i].extract_data()
                assert pkgdata.data['python_versions'] == expected

    @staticmethod
    @me.process_description
    def desciption_fce(description):
        return description

    @pytest.mark.parametrize(('desc', 'expected'), [
        (
'''Convert Python packages to RPM SPECFILES. The packages can be downloaded from
PyPI and the produced SPEC is in line with Fedora Packaging Guidelines or
Mageia Python Policy.Users can provide their own templates for rendering the
package metadata. Both the package source and metadata can be extracted from
PyPI or from local filesystem (local file doesn't provide that much information
    though).''',
'''Convert Python packages to RPM SPECFILES. The packages can be downloaded from \
PyPI and the produced SPEC is in line with Fedora Packaging Guidelines or \
Mageia Python Policy.Users can provide their own templates for rendering the \
package metadata. Both the package source and metadata can be extracted from \
PyPI or from local filesystem (local file doesn't provide that much information \
though).'''),
        (
'''Vex
###

Run a command in the named virtualenv.

vex is an alternative to virtualenv's ``source wherever/bin/activate``
and ``deactivate``, and virtualenvwrapper's ``workon``, and also
virtualenv-burrito if you use that.''',
'''Run a command in the named virtualenv.vex is an alternative to virtualenv's \
source wherever/bin/activate and deactivate, and virtualenvwrapper's workon, \
and also virtualenv-burrito if you use that.'''),
        (
'''Python bindings to the OpenStack Cinder API
===========================================

.. image:: https://img.shields.io/pypi/v/python-cinderclient.svg
    :target: https://pypi.python.org/pypi/python-cinderclient/
    :alt: Latest Version

.. image:: https://img.shields.io/pypi/dm/python-cinderclient.svg
    :target: https://pypi.python.org/pypi/python-cinderclient/
    :alt: Downloads

This is a client for the OpenStack Cinder API. There's a Python API (the
``cinderclient`` module), and a command-line script (``cinder``). Each
implements 100% of the OpenStack Cinder API.''',
'''Python bindings to the OpenStack Cinder API This is a client for the OpenStack \
Cinder API. There's a Python API (the cinderclient module), and a command-line \
script (cinder). Each implements 100% of the OpenStack Cinder API.'''),
        (
'''.. image:: http://pytest.org/latest/_static/pytest1.png
   :target: http://pytest.org
   :align: center
   :alt: pytest

------

.. image:: https://img.shields.io/pypi/v/pytest.svg
   :target: https://pypi.python.org/pypi/pytest
.. image:: https://img.shields.io/pypi/pyversions/pytest.svg
  :target: https://pypi.python.org/pypi/pytest
.. image:: https://img.shields.io/coveralls/pytest-dev/pytest/master.svg
   :target: https://coveralls.io/r/pytest-dev/pytest
.. image:: https://travis-ci.org/pytest-dev/pytest.svg?branch=master
    :target: https://travis-ci.org/pytest-dev/pytest
.. image:: https://ci.appveyor.com/api/projects/status/mrgbjaua7t33pg6b?svg=true
    :target: https://ci.appveyor.com/project/pytestbot/pytest

The ``pytest`` framework makes it easy to write small tests, yet
scales to support complex functional testing for applications and libraries.

An example of a simple test:

.. code-block:: python

    # content of test_sample.py
    def func(x):
        return x + 1

    def test_answer():
        assert func(3) == 5


To execute it::

    $ py.test
    ======= test session starts ========
    platform linux -- Python 3.4.3, pytest-2.8.5, py-1.4.31, pluggy-0.3.1
    collected 1 items''',
''' The pytest framework makes it easy to write small tests, yet scales to support \
complex functional testing for applications and libraries.An \
example of a simple test:.. code-block:: python content of test_sample.py def func(x): return \
x + 1 def test_answer(): assert func(3) 5 To execute it:: $ py.test test \
session starts platform linux -- Python 3.4.3, pytest-2.8.5, py-1.4.31, pluggy-0.3.1 \
collected 1 items'''),
        (
'''Some description text, http://docs.openstack.org/developer/python-designateclient/.
the rest of meaningful text...''',
'''Some description text, the rest of meaningful text...''')
    ])
    def test_process_description(self, desc, expected):
        assert set(self.desciption_fce(desc)
                   .split('\n')) == set(expected.split('\n'))

    @pytest.mark.parametrize(('text', 'length', 'delim', 'expected'), [
        (
'''Allow to inject warning filters during ``nosetest``.  Put the same arguments
as ``warnings.filterwarnings`` in ``setup.cfg`` at the root of your project.
Separated each argument by pipes ``|``, one filter per line. Whitespace are
stripped.  for example:  ::      [nosetests]     warningfilters=default
''', 50, '.', "Allow to inject warning filters during ``nosetest``")
    ])
    def test_cut_to_length(self, text, length, delim, expected):
        assert me.cut_to_length(text, length, delim) == expected

    @pytest.mark.parametrize(('i', 'expected'), [
        (0, False),
        (1, True),
        (2, True),
        (3, False),
        (4, False),
    ])
    def test_has_test_files(self, i, expected):
        with self.e[i].archive:
            assert self.e[i].has_test_files == expected


class TestPyPIMetadataExtension(object):
    td_dir = '{0}/test_data/'.format(tests_dir)
    client = flexmock(
        release_urls=lambda n, v: [
            {'md5_digest': '9a7a2f6943baba054cf1c28e05a9198e',
             'url': 'https://files.pythonhosted.org/packages/source/r/restsh/restsh-0.1.tar.gz'}],
        release_data=lambda n, v: {
            'description': 'UNKNOWN',
            'release_url': 'http://pypi.python.org/pypi/restsh/0.1',
            'classifiers': ['Development Status :: 4 - Beta',
                            'Intended Audience :: Developers',
                            'License :: OSI Approved :: BSD License',
                            'Operating System :: OS Independent'
                            ],
            'license': 'BSD',
            'summary': 'A simple rest shell client',
            'spam': 'eggs and beans'
            }
    )

    def setup_method(self, method):
        self.nc = NameConvertor('fedora')
        # we will only test getting stuff from the client => pass spam as file
        self.e = me.SetupPyMetadataExtractor(
            '{0}pytest-2.2.3.zip'.format(self.td_dir), 'pytest',
            self.nc, '2.2.3')

    @pytest.mark.parametrize(('what', 'expected'), [
        ('description',
         'cross-project testing tool for Python.Platforms: Linux, Win32, '
         'OSXInterpreters: Python versions 2.4 through to 3.2, Jython 2.5.1 '
         'and PyPy-1.6/1.7Bugs and issues: page: (c) Holger Krekel and others, 2004-2012'),
        ('md5', '9a7a2f6943baba054cf1c28e05a9198e'),
        ('source0',
         'https://files.pythonhosted.org/packages/source/p/pytest/restsh-0.1.tar.gz'),
        ('license', 'MIT license'),
        ('summary', 'py.test: simple powerful testing with Python')
    ])
    def test_extract(self, what, expected):
        data = self.e.extract_data(self.client)
        assert getattr(data, what) == expected


class TestSetupPyMetadataExtractor(object):
    td_dir = '{0}/test_data/'.format(tests_dir)

    def setup_method(self, method):
        self.nc = NameConvertor('fedora')
        self.e = []
        for archive in ('plumbum-0.9.0.tar.gz',
                        'pytest-2.2.3.zip',
                        'simpleeval-0.8.7.tar.gz',
                        'coverage_pth-0.0.1.tar.gz',
                        'utest-0.1.0.tar.gz'):
            name, version = archive.split('-')
            self.e.append(me.SetupPyMetadataExtractor('{0}{1}'.format(
                self.td_dir, archive), name, self.nc, version[:5]))

    @pytest.mark.parametrize(('i', 'what', 'expected'), [
        (0, 'runtime_deps', [['Requires', 'python-six', '{name}']]),
        (0, 'build_deps', [['BuildRequires', 'python2-devel', '{name}'],
                           ['BuildRequires', 'python-setuptools', '{name}']]),
        (0, 'py_modules', []),
        (0, 'packages', ['plumbum']),
        (0, 'scripts', []),
        (0, 'home_page', "https://github.com/tomerfiliba/plumbum"),
        (0, 'summary', "Plumbum: shell combinators library"),
        (0, 'license', 'MIT'),
        (0, 'has_pth', False),
        (0, 'has_extension', False),
        (0, 'has_test_suite', False),
        (0, 'has_bundled_egg_info', True),
        (0, 'doc_files', ['README.rst']),
        (0, 'doc_license', ['LICENSE']),
        (0, 'sphinx_dir', None),
        (0, 'source0', 'plumbum-0.9.0.tar.gz'),
        (1, 'runtime_deps', [['Requires', 'python-py', '{name} >= 1.4.7~dev2'],
                             ['Requires', 'python-setuptools', '{name}']]),
        (1, 'build_deps', [['BuildRequires', 'python2-devel', '{name}'],
                           ['BuildRequires', 'python-py', '{name} >= 1.4.7~dev2'],
                           ['BuildRequires', 'python-setuptools', '{name}'],
                           ['BuildRequires', 'python-sphinx', '{name}']]),
        (1, 'py_modules', ['pytest']),
        (1, 'packages', ['_pytest']),
        (1, 'home_page', 'http://pytest.org'),
        (1, 'summary', 'py.test: simple powerful testing with Python'),
        (1, 'license', 'MIT license'),
        (1, 'has_pth', False),
        (1, 'has_extension', False),
        (1, 'has_test_suite', True),
        (1, 'has_packages', True),
        (1, 'has_bundled_egg_info', True),
        (1, 'doc_files', ['README.txt']),
        (1, 'doc_license', ['LICENSE']),
        (1, 'sphinx_dir', 'doc'),
        (1, 'source0', 'pytest-2.2.3.zip'),
        (2, 'py_modules', ['simpleeval']),
        (3, 'runtime_deps', [['Requires', 'python-coverage', '{name}']]),
        (3, 'python_versions', []),
        (4, 'runtime_deps', [['Requires', 'python-pyp2rpm',
                              '({name} >= 3.3.1 with {name} < 3.4)']]),
    ])
    def test_extract(self, i, what, expected):
        data = self.e[i].extract_data()
        assert getattr(data, what) == expected

    @pytest.mark.parametrize(('doc_files', 'license', 'other'), [
        (['LICENSE', 'README'], ['LICENSE'], ['README']),
        ([], [], []),
        (['README', 'DESCRIPTION'], [], ['README', 'DESCRIPTION']),
        (['LICENSE', './dir/LICENSE', 'README'],
         ['LICENSE', './dir/LICENSE'], ['README']),
        (['LICENSE.MIT', './LICENSE.CC-BY-SA-3.0'],
         ['LICENSE.MIT', './LICENSE.CC-BY-SA-3.0'], []),
        (['README', 'COPYRIGHT'], ['COPYRIGHT'], ['README']),
        (['COPYRIGHT.txt'], ['COPYRIGHT.txt'], []),
        (['README', 'COPYING'], ['COPYING'], ['README']),
    ])
    def test_doc_files(self, doc_files, license, other):
        flexmock(me.SetupPyMetadataExtractor).should_receive(
            'doc_files').and_return(doc_files)
        data = self.e[0].extract_data()
        assert data.data['doc_license'] == license
        assert data.data['doc_files'] == other


class TestWheelMetadataExtractor(object):
    td_dir = '{0}/test_data/'.format(tests_dir)

    def setup_method(self, method):
        self.nc = NameConvertor('fedora')
        self.e = []
        for archive, name, version in [
                ('setuptools-19.6-py2.py3-none-any.whl',
                 'setuptools', '19.6.2'),
                ('py2exe-0.9.2.2-py33.py34-none-any.whl',
                 'py2exe', '0.9.2.2')]:
            self.e.append(me.WheelMetadataExtractor('{0}{1}'.format(
                self.td_dir, archive), name, self.nc, version, venv=False))

    @pytest.mark.parametrize(('i', 'what', 'expected'), [
        (0, 'runtime_deps', [['Requires', 'python-certifi', '{name} == 2015.11.20'],
                             ['Requires', 'python-setuptools', '{name}']]),
        (0, 'build_deps', [['BuildRequires', 'python2-devel', '{name}'],
                           ['BuildRequires', 'python-pytest', '{name} >= 2.8'],
                           ['BuildRequires', 'python-setuptools[ssl]', '{name}'],
                           ['BuildRequires', 'python-certifi', '{name} == 2015.11.20'],
                           ['BuildRequires', 'python-setuptools', '{name}']]),

        (0, 'py_modules', ['_markerlib', 'pkg_resources', 'setuptools']),
        (0, 'packages', ['setuptools']),
        (0, 'scripts', []),
        (0, 'home_page', 'https://bitbucket.org/pypa/setuptools'),
        (0, 'summary', 'Easily download, build, install, upgrade, and uninstall Python packages'),
        (0, 'license', 'TODO:'),
        (0, 'has_pth', False),
        (0, 'has_extension', False),
        (0, 'has_test_suite', True),
        (0, 'doc_files', ['DESCRIPTION.rst']),
        (0, 'doc_license', []),
        (0, 'sphinx_dir', None),
        (0, 'python_versions', ['2', '3']),
        (1, 'runtime_deps', [['Requires', 'python-setuptools', '{name}']]),
        (1, 'build_deps', [['BuildRequires', 'python2-devel', '{name}'],
                           ['BuildRequires', 'python-setuptools', '{name}']]),
        (1, 'py_modules', ['py2exe']),
        (1, 'packages', ['py2exe']),
        (1, 'scripts', ['build_exe-script.py', 'build_exe.exe']),
        (1, 'home_page', 'TODO:'),
        (1, 'summary', 'Build standalone executables for Windows (python 3 version)'),
        (1, 'license', 'MIT/X11'),
        (1, 'has_pth', False),
        (1, 'has_extension', False),
        (1, 'has_test_suite', False),
        (1, 'doc_files', []),
        (1, 'doc_license', []),
        (1, 'sphinx_dir', None),
        (1, 'python_versions', ['3']),

    ])
    def test_extract(self, i, what, expected):
        data = self.e[i].extract_data()
        assert getattr(data, what) == expected

    @pytest.mark.parametrize(("input", "expected"), [
       ([], ""),
       (['License :: OSI Approved :: Python Software Foundation License'],
        'Python'),
       (['Classifier: License :: OSI Approved :: Python Software Foundation License'],
        'Python'),
       (['License :: OSI Approved :: GNU General Public License v2 or later (GPLv2+)',
         'License :: OSI Approved :: MIT License'], 'GPLv2+ and MIT'),
    ])
    def test_license_from_trove(self, input, expected):
        assert me.license_from_trove(input) == expected
