import functools

from pyp2rpmlib import settings

def memoize_by_args(func):
    """Memoizes return value of a func based on args."""
    memory = {}

    @functools.wraps(func)
    def memoized(*args):
        if not args in memory.keys():
            value = func(*args)
            memory[args] = value

        return memory[args]

    return memoized

def rpm_versioned_name(name, version):
    """Properly versions the name.
    For example:
    rpm_versioned_name('python-foo', '26') will return python26-foo
    rpm_versioned_name('pyfoo, '3') will return python3-pyfoo

    Args:
        name: name to version
        version: version or None
    Returns:
        Versioned name or the original name if given version is None.
    """
    versioned_name = name
    if version:
        if name.startswith('python-'):
            versioned_name = name.replace('python-', 'python%s-' % version)
        else:
            versioned_name = 'python%s-%s' % (version, name)

    return versioned_name

def rpm_name(name, python_version = None):
    """Returns name of the package coverted to (possibly) correct package name according to Packaging Guidelines.
    Args:
        name: name to convert
        python_version: python version for which to retrieve the name of the package
    Returns:
        Converted name of the package, that should be in line with Fedora Packaging Guidelines.
        If for_python is not None, the returned name is in form python%(version)s-%(name)s
    """
    rpmized_name = name

    if name.lower().find('py') == -1: # name doesn't contain "py" => prefix with "python-"
        rpmized_name = 'python-%s' % name
    elif name.endswith('-python'): # name ends with "-python" => strip that and put it to front
        rpmized_name = 'python-%s' % name.replace('-python', '')
    # else the name contains "py" as its part => do nothing
    # or the name is in form "python-%(name)s", which is fine, toO

    return rpm_versioned_name(rpmized_name, python_version)

def license_from_trove(trove):
    """Finds out license from list of trove classifiers.
    Args:
        trove: list of trove classifiers
    Returns:
        Fedora name of the package license or empty string, if no licensing information is found in trove classifiers.
    """
    license = []
    for classifier in trove:
        if classifier.find('License') != -1:
            stripped = classifier.strip()
            # if taken from EGG-INFO, begins with Classifier:
            stripped = stripped[stripped.find('License'):]
            if settings.TROVE_LICENSES.has_key(stripped):
                license.append(settings.TROVE_LICENSES[stripped])
    return ' and '.join(license)
