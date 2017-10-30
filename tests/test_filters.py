import pytest

from pyp2rpm.filters import (macroed_pkg_name,
                             name_for_python_version,
                             script_name_for_python_version)


class TestFilters(object):

    @pytest.mark.parametrize(('pkg_name', 'srcname', 'version',
                              'default_number', 'expected'), [
        ('python-Jinja2', None, '2', False, 'python2-%{pypi_name}'),
        ('python-Jinja2', None, '2', True, 'python2-%{pypi_name}'),
        ('python-Jinja2', None, '3', False, 'python-%{pypi_name}'),
        ('python-Jinja2', None, '3', True, 'python3-%{pypi_name}'),
        ('python-stdnum', 'stdnum', '2', False, 'python2-%{srcname}'),
        ('python-stdnum', 'stdnum', '2', True, 'python2-%{srcname}'),
        ('python-stdnum', 'stdnum', '3', False, 'python-%{srcname}'),
        ('python-stdnum', 'stdnum', '3', True, 'python3-%{srcname}')
    ])
    def test_macroed_pkg_name(self, pkg_name, srcname, version,
                              default_number, expected):
        assert name_for_python_version(macroed_pkg_name(
            pkg_name, srcname), version, default_number) == expected

    @pytest.mark.parametrize(('name', 'version', 'minor',
                              'default_number', 'expected'), [
        ('foo', '2', False, False, 'foo-2'),
        ('foo', '2', False, True, 'foo-2'),
        ('foo', '3', False, False, 'foo'),
        ('foo', '3', False, True, 'foo-3'),
        ('foo', '35', True, True, 'foo-3.5'),
        ('foo', '3', True, True, 'foo-%{python3_version}'),
    ])
    def test_script_name_for_python_version(self, name, version, minor,
                                            default_number, expected):
        assert script_name_for_python_version(name, version, minor,
                                              default_number) == expected
