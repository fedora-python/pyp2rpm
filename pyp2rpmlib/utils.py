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

def rpm_name(name):
    """Returns name of the package coverted to (possibly) correct package name according to Packaging Guidelines.
    Args:
        name: name to convert
    Returns:
        Converted name of the package, that should be in line with Fedora Packaging Guidelines.
    """
    if name.lower().find('py') != -1:
        return name
    else:
        return 'python-%s' % name

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
            if settings.TROVE_LICENSES.has_key(classifier):
                license.append(settings.TROVE_LICENSES[classifier])
    return ' and '.join(license)
