from pyp2rpmlib import utils

def for_python_version(name, version):
    return utils.rpm_name(name, version)

def macroed_pkg_name(name):
    if name.startswith('python-'):
        return 'python-%{pypi_name}'
    else:
        return '%{pypi_name}'

__all__ = [for_python_version, macroed_pkg_name]
