import functools

from pyp2rpm import settings


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


def license_from_trove(trove):
    """Finds out license from list of trove classifiers.
    Args:
        trove: list of trove classifiers
    Returns:
        Fedora name of the package license or empty string, if no licensing information is found in trove classifiers.
    """
    license = []
    for classifier in trove:
        if 'License' in classifier != -1:
            stripped = classifier.strip()
            # if taken from EGG-INFO, begins with Classifier:
            stripped = stripped[stripped.find('License'):]
            if stripped in settings.TROVE_LICENSES:
                license.append(settings.TROVE_LICENSES[stripped])
    return ' and '.join(license)
