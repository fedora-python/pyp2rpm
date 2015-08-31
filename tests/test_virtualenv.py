import pytest
import os
import shutil
import tempfile
from flexmock import flexmock
from pyp2rpm.virtualenv import *
from pyp2rpm.name_convertor import NameConvertor
from pyp2rpm.settings import DEFAULT_DISTRO

class TestUtils(object):
    @pytest.mark.parametrize(('input', 'expected'), [
        (['foo', 'foo-1.0.0.dist-info'], set(['foo'])),
        (['foo', 'foo-1.0.0.dist-info', 'foo2'], set(['foo', 'foo2'])),
        (['foo', 'foo-1.0.0.dist-info', 'foo2-1.0.0-py2.7.egg-info'],
         set(['foo', 'foo2-1.0.0-py2.7.egg-info'])),
        (['foo', 'foo2-1.0.0-py2.7.egg-info'], set(['foo', 'foo2-1.0.0-py2.7.egg-info'])),
        ([], set()),
    ])
    def test_site_packages_filter(self, input, expected):
        assert site_packages_filter(input) == expected

    @pytest.mark.parametrize(('deps_list', 'package', 'expected'), [
        ([('foo', '1.0'), ('dep1', '1.0')], 'fOO', [('dep1', '1.0')]),
        ([('Foo', '1.0'), ('dep1', '1.0'), ('dep2', '1.0')], 'foo',
         [('dep1', '1.0'), ('dep2', '1.0')]),
    ])
    def test_deps_package_filter(self, deps_list, package, expected):
        assert deps_package_filter(deps_list, package) == expected

    @pytest.mark.parametrize(('input', 'expected'), [
        ([('foo', '1.0'), ('wheel', '0.24.0')], [('foo', '1.0')]),
        ([('foo', '1.0'), ('foo2', '1.0')], [('foo', '1.0'), ('foo2', '1.0')]),
        ([('foo', '1.0'), ('foo2', '1.0')], [('foo', '1.0'), ('foo2', '1.0')]),
        ([], []),
    ])
    def test_deps_wheel_filter(self, input, expected):
        assert deps_wheel_filter(input) == expected


class TestDirsContent(object):
    @pytest.mark.parametrize(('before', 'after', 'expected'), [
        (set(['activate', 'pip']), set(['activate', 'pip', 'foo']), set(['foo'])),
        (set(['activate', 'pip']), set(['activate', 'pip']), set()),
    ])
    def test_sub_bin(self, before, after, expected):
        result = DirsContent(bindir=after, lib_sitepackages=set([])) -\
        DirsContent(bindir=before, lib_sitepackages=set([]))
        assert result.bindir == expected

    @pytest.mark.parametrize(('before', 'after', 'expected'), [
        (set(['setuptools', 'pip']), set(['setuptools', 'pip', 'foo']), set(['foo'])),
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
        self.venv = VirtualEnv(None, self.temp_dir, NameConvertor(DEFAULT_DISTRO))

    def teardown_method(self, method):
        shutil.rmtree(self.temp_dir)

    @pytest.mark.parametrize(('input', 'expected'), [
        ([('foo', '1.0')], [['Requires', 'python-foo']]),
        ([('foo', '1.0'), ('foo2', '1.0')], [['Requires', 'python-foo'], ['Requires', 'python-foo2']]),
        ([], []),
    ])
    def test_change_deps_format(self, input, expected):
        flexmock(NameConvertor).should_receive('rpm_name').replace_with(lambda
            x: 'python-' + x)
        assert self.venv.change_deps_format(input) == expected

    @pytest.mark.parametrize(('bin_diff', 'package_diff', 'expected'), [
        (set(['foo']), set(['foo']), (set(['foo']), ['foo'])),
        (set([]), set(['foo', 'foo2']), (set(['foo', 'foo2']), [])),
        (set(['foo']), set([]), (set([]), ['foo'])),
    ])
    def test_get_dirs_defferance(self, bin_diff, package_diff, expected):
        flexmock(DirsContent).should_receive('__sub__').and_return(DirsContent(bin_diff, package_diff))
        assert self.venv.get_dirs_differance == expected
