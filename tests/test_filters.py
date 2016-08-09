import pytest

from pyp2rpm.filters import macroed_pkg_name, name_for_python_version


class TestFilters(object):

    @pytest.mark.parametrize(('pkg_name', 'name', 'version', 'default_number', 'expected'), [
        ('python-Jinja2', 'Jinja2', '2', False, 'python-%{pypi_name}'),
        ('python-Jinja2', 'Jinja2', '2', True, 'python2-%{pypi_name}'),
        ('python-Jinja2', 'Jinja2', '3', False, 'python3-%{pypi_name}'),
        ('python-Jinja2', 'Jinja2', '3', True, 'python3-%{pypi_name}'),
        ('python-stdnum', 'python-stdnum', '2', False, 'python-stdnum'),
        ('python-stdnum', 'python-stdnum', '2', True, 'python2-stdnum'),
        ('python-stdnum', 'python-stdnum', '3', False, 'python3-stdnum')
    ])
    def test_macroed_pkg_name(self, pkg_name, name, version, default_number, expected):
        assert name_for_python_version(macroed_pkg_name(
            pkg_name, name), version, default_number) == expected
