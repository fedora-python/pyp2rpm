import pytest
import shutil
import tempfile
from flexmock import flexmock
try:
    from pyp2rpm.virtualenv import (DirsContent,
                                    VirtualEnv,
                                    site_packages_filter,
                                    scripts_filter)
except ImportError:
    VirtualEnv = None
from pyp2rpm.name_convertor import NameConvertor
from pyp2rpm.settings import DEFAULT_DISTRO, DEFAULT_PYTHON_VERSION

pytestmark = pytest.mark.skipif(VirtualEnv is None,
                                reason="virtualenv-api not installed")


class TestUtils(object):

    @pytest.mark.parametrize(('input', 'expected'), [
        (['foo', 'foo-1.0.0.dist-info'], set(['foo'])),
        (['foo', 'foo-1.0.0.dist-info', 'foo2'], set(['foo', 'foo2'])),
        (['foo', 'foo-1.0.0.dist-info', 'foo2-1.0.0-py2.7.egg-info'],
         set(['foo'])),
        (['foo', 'foo2-1.0.0-py2.7.egg-info'],
         set(['foo'])),
        ([], set()),
    ])
    def test_site_packages_filter(self, input, expected):
        assert site_packages_filter(input) == expected

    @pytest.mark.parametrize(('input', 'expected'), [
        (['script', 'script2'], ['script', 'script2']),
        (['script.py', 'script2'], ['script.py', 'script2']),
        (['script.pyc', 'script2'], ['script2']),
        (['script.pyc'], []),
        ([], []),
    ])
    def test_scripts_filter(self, input, expected):
        assert scripts_filter(input) == expected


class TestDirsContent(object):

    @pytest.mark.parametrize(('before', 'after', 'expected'), [
        (set(['activate', 'pip']), set(['activate', 'pip', 'foo']),
         set(['foo'])),
        (set(['activate', 'pip']), set(['activate', 'pip']), set()),
    ])
    def test_sub_bin(self, before, after, expected):
        result = DirsContent(bindir=after, lib_sitepackages=set([])) -\
            DirsContent(bindir=before, lib_sitepackages=set([]))
        assert result.bindir == expected

    @pytest.mark.parametrize(('before', 'after', 'expected'), [
        (set(['setuptools', 'pip']), set(['setuptools', 'pip', 'foo']),
         set(['foo'])),
        (set(['wheel', 'pip']), set(['foo', 'pip']), set(['foo'])),
        (set(['wheel', 'pip']), set(['pip']), set()),
    ])
    def test_sub_sitepackages(self, before, after, expected):
        result = DirsContent(lib_sitepackages=after, bindir=set([])) -\
            DirsContent(lib_sitepackages=before, bindir=set([]))
        assert result.lib_sitepackages == expected


class TestVirtualEnv(object):

    def setup_method(self, method):
        self.temp_dir = tempfile.mkdtemp()
        self.venv = VirtualEnv(name=None, version=None,
                               temp_dir=self.temp_dir,
                               name_convertor=NameConvertor(DEFAULT_DISTRO),
                               base_python_version=DEFAULT_PYTHON_VERSION)

    def teardown_method(self, method):
        shutil.rmtree(self.temp_dir)

    @pytest.mark.parametrize(('bin_diff', 'package_diff', 'expected'), [
        (set(['foo']), set(['foo']), (['foo'], [], ['foo'], False)),
        (set(['foo']), set(['foo.py', 'foo.pyc']),
         ([], ['foo'], ['foo'], False)),
        (set([]), set(['foo.py']), ([], ['foo'], [], False)),
        (set(['foo']), set(["foo-pyX.Y-nspkg.pth"]),
         ([], [], ['foo'], True)),
        (set(), set(), ([], [], [], False)),
    ])
    def test_get_dirs_differance(self, bin_diff, package_diff, expected):
        flexmock(DirsContent).should_receive('__sub__').and_return(
            DirsContent(bin_diff, package_diff))
        self.venv.get_dirs_differance()
        assert ((self.venv.data['packages'],
                 self.venv.data['py_modules'],
                 self.venv.data['scripts'],
                 self.venv.data['has_pth']) == expected)
