import pytest

from pyp2rpm.filters import macroed_pkg_name, name_for_python_version


class TestFilters(object):

    @pytest.mark.parametrize(('pkg_name', 'srcname', 'version', 'default_number', 'expected'), [
        ('python-Jinja2', None, '2', False, 'python-%{pypi_name}'),
        ('python-Jinja2', None, '2', True, 'python2-%{pypi_name}'),
        ('python-Jinja2', None, '3', False, 'python3-%{pypi_name}'),
        ('python-Jinja2', None, '3', True, 'python3-%{pypi_name}'),
        ('python-stdnum', 'stdnum', '2', False, 'python-%{srcname}'),
        ('python-stdnum', 'stdnum', '2', True, 'python2-%{srcname}'),
        ('python-stdnum', 'stdnum', '3', False, 'python3-%{srcname}')
    ])
    def test_macroed_pkg_name(self, pkg_name, srcname, version, default_number, expected):
        assert name_for_python_version(macroed_pkg_name(
            pkg_name, srcname), version, default_number) == expected
