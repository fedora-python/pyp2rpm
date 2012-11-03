from pyp2rpm import utils
from pyp2rpm import settings

def name_for_python_version(name, version):
    return utils.rpm_name(name, version)

def script_name_for_python_version(name, version):
    if version == settings.DEFAULT_PYTHON_VERSION:
        return name
    else:
        return 'python%s-%s' % (version, name)

def sitedir_for_python_version(name, version):
    if version == settings.DEFAULT_PYTHON_VERSION:
        return name
    else:
        return name.replace('python', 'python%s' % version)

def python_bin_for_python_version(name, version):
    if version == settings.DEFAULT_PYTHON_VERSION:
        return name
    else:
        return name.replace('__python', '__python3')

def macroed_pkg_name(name):
    if name.startswith('python-'):
        return 'python-%{pypi_name}'
    else:
        return '%{pypi_name}'

__all__ = [name_for_python_version,
           script_name_for_python_version,
           sitedir_for_python_version,
           python_bin_for_python_version,
           macroed_pkg_name]
