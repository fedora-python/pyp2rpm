import os
import tempfile
import shutil

import pytest

from flexmock import flexmock

try:
    import xmlrpclib
except ImportError:
    import xmlrpc.client as xmlrpclib

from pyp2rpm.package_getters import *
from pyp2rpm.exceptions import *
from pyp2rpm import settings

tests_dir = os.path.split(os.path.abspath(__file__))[0]


class TestPackageGetters(object):
    client = xmlrpclib.ServerProxy(settings.PYPI_URL)

    @pytest.mark.parametrize(('name', 'version', 'wheel', 'hf', 'expected_url', 'expected_md5'), [
        ('setuptools', '18.3.1', False, False,
         'https://files.pythonhosted.org/packages/source/s/setuptools/setuptools-18.3.1.tar.gz',
         '748187b93152fa60287dfb896837fd7c'),
        ('setuptools', '18.3.1', True, False,
         'https://files.pythonhosted.org/packages/source/s/setuptools/setuptools-18.3.1-py2.py3-none-any.whl',
         'a21a4d02d0bab2eac499cca72faeb076'),
        ('setuptools', '18.3.1', False, True,
         'https://pypi.python.org/packages/86/8a/c4666b05c74e840eb9b09d28f4e7ae76fc9075e8c653d0eb4d265a5b49d9/setuptools-18.3.1.tar.gz',
         '748187b93152fa60287dfb896837fd7c'),
        ('pypandoc', '1.1.3', False, False,
         'https://files.pythonhosted.org/packages/source/p/pypandoc/pypandoc-1.1.3.zip',
         '771f376bf9c936a90159cd94235998c2'),
    ])
    @pytest.mark.webtest
    def test_get_url(self, name, version, wheel, hf, expected_url, expected_md5):
        assert (expected_url, expected_md5) == get_url(self.client, name, version, wheel, hf)

    @pytest.mark.parametrize(('name', 'version', 'wheel', 'hf', 'exception', 'error_msg'), [
        ('nonexistent_pkg', '0.0.0', False, False, MissingUrlException,
         'Url of source archive not found.'),
        ('Pymacs', '0.25', False, False, MissingUrlException,
         'Pymacs package has no sources on PyPI, Please ask the maintainer to upload sources.'),
    ])
    @pytest.mark.webtest
    def test_get_url_raises(self, name, version, wheel, hf, exception, error_msg):
        with pytest.raises(exception) as exc_info:
            get_url(self.client, name, version, wheel, hf)
        assert error_msg == str(exc_info.value)


class TestPypiFileGetter(object):
    client = flexmock(
        package_releases=lambda n: n == 'spam' and ['2', '1'] or [],
        release_urls=lambda n, v: n == 'spam' and v in ['2', '1'] and [{'url': 'spam'}] or []
    )

    @pytest.mark.parametrize(('name', 'version'), [
        ('eggs', '2'),
        ('spam', '3'),
    ])
    def test_init_bad_data(self, name, version):
        with pytest.raises(NoSuchPackageException):
            PypiDownloader(self.client, name, version)

    @pytest.mark.parametrize(('name', 'version', 'expected_ver'), [
        ('spam', '1', '1'),
        ('spam', None, '2'),
    ])
    def test_init_good_data(self, name, version, expected_ver):
        d = PypiDownloader(self.client, name, version)
        assert d.version == expected_ver


class TestLocalFileGetter(object):
    td_dir = '{0}/test_data/'.format(tests_dir)

    def setup_method(self, method):
        self.l = [LocalFileGetter('{0}plumbum-0.9.0.tar.gz'.format(self.td_dir)),
                  LocalFileGetter('{0}Sphinx-1.1.3-py2.6.egg'.format(self.td_dir)),
                  LocalFileGetter('{0}unextractable-1.tar'.format(self.td_dir)),
                  LocalFileGetter('{0}setuptools-19.6-py2.py3-none-any.whl'.format(self.td_dir)),
                  LocalFileGetter('{0}py2exe-0.9.2.2-py33.py34-none-any.whl'.format(self.td_dir)),
                  LocalFileGetter('python-foo-1.tar'),
                  LocalFileGetter('python-many-dashes-foo-1.tar'),
                  ]

    def teardown_method(self, method):
        for file_getter in self.l:
            if hasattr(file_getter, 'temp_dir'):
                shutil.rmtree(file_getter.temp_dir)

    @pytest.mark.parametrize(('i', 'expected'), [
        (0, 'plumbum-0.9.0'),
        (1, 'Sphinx-1.1.3-py2.6'),
        (2, 'unextractable-1'),
        (3, 'setuptools-19.6-py2.py3-none-any'),
        (4, 'py2exe-0.9.2.2-py33.py34-none-any'),
    ])
    def test__stripped_name_version(self, i, expected):
        assert self.l[i]._stripped_name_version == expected

    @pytest.mark.parametrize(('i', 'expected'), [
        (0, 'plumbum-0.9.0'),
        (1, 'Sphinx-1.1.3-py2.6'),
        (2, 'unextractable-1'),
        (3, 'setuptools-19.6-py2.py3-none-any'),
        (4, 'py2exe-0.9.2.2-py33.py34-none-any'),
    ])
    def test__stripped_name_version(self, i, expected):
        assert self.l[i]._stripped_name_version == expected

    @pytest.mark.parametrize(('i', 'expected'), [
        (0, ('plumbum', '0.9.0')),
        (1, ('Sphinx', '1.1.3')),
        (3, ('setuptools', '19.6')),
        (4, ('py2exe', '0.9.2.2')),
        (5, ('python-foo', '1')),
        (6, ('python-many-dashes-foo', '1')),
    ])
    def test_get_name_version(self, i, expected):
        assert self.l[i].get_name_version() == expected

    def test_get_non_existent_file(self):
        with pytest.raises(EnvironmentError):
            LocalFileGetter('/this/path/doesnot/exist', tempfile.gettempdir()).get()

    def test_get_existent_file(self):
        tmpdir = tempfile.gettempdir()
        in_tmp_dir = os.path.join(tmpdir, 'plumbum-0.9.0.tar.gz')
        self.l[0].save_dir = tmpdir
        if os.path.exists(in_tmp_dir):
            os.unlink(in_tmp_dir)
        assert self.l[0].get() == in_tmp_dir
        assert os.path.exists(self.l[0].get())
        os.unlink(in_tmp_dir)

    def test_get_to_same_location(self):
        tmpdir = tempfile.gettempdir()
        self.l[1].save_dir = self.td_dir
        assert os.path.samefile(self.l[1].get(), os.path.join(
            self.td_dir, 'Sphinx-1.1.3-py2.6.egg'))
        assert not os.path.exists(os.path.join(tmpdir, 'Sphinx-1.1.3-py2.6.egg'))
