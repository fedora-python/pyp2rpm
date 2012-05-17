import functools

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
