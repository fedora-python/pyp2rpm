from pyp2rpm import settings
from pyp2rpm import name_convertor


def name_for_python_version(name, version, default_number=False, epel=False):
    return name_convertor.NameConvertor.rpm_versioned_name(name, version, default_number, epel)


def script_name_for_python_version(name, version, minor=False, default_number=True):
    if not default_number:
        if version == settings.DEFAULT_PYTHON_VERSION:
            return name
    if minor:
        if len(version) > 1:
            return '{0}-{1}'.format(name, '.'.join(list(version)))
        else:
            return '{0}-%{{python{1}_version}}'.format(name, version)
    else:
        return '{0}-{1}'.format(name, version[0])


def sitedir_for_python_version(name, version, default_string='python2'):
    if version == settings.DEFAULT_PYTHON_VERSION:
        return name
    else:
        return name.replace(default_string, 'python{0}'.format(version))


def python_bin_for_python_version(name, version, default_string='__python2'):
    if version == settings.DEFAULT_PYTHON_VERSION:
        return name
    else:
        return name.replace(default_string, '__python{0}'.format(version))


def macroed_pkg_name(pkg_name, name):
    if pkg_name.startswith('python') and name == pkg_name:
        # if (pypi) name starts with python also then we can't prefix python
        # this would lead to python3-python-foo names like
        return name
    elif pkg_name.startswith('python-'):
        return 'python-%{pypi_name}'
    else:
        return '%{pypi_name}'


def module_to_path(name, module):
    module = module.replace(".", "/")
    if name == module:
        return "%{pypi_name}"
    else:
        return module


def package_to_path(package, module):
    # this is used only on items in data.packages
    # if package name differs from module name than it is a subpackage
    # and we have to list it in %files section
    if package == module:
        return "%{pypi_name}"
    else:
        return package.replace('-', '_')

__all__ = [name_for_python_version,
           script_name_for_python_version,
           sitedir_for_python_version,
           python_bin_for_python_version,
           macroed_pkg_name,
           module_to_path,
           package_to_path]
