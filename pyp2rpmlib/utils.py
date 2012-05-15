import functools

def memoize_by_args(func):
    memory = {}

    @functools.wraps(func)
    def memoized(*args):
        if not args in memory.keys():
            value = func(*args)
            memory[args] = value

        return memory[args]

    return memoized

def rpm_name(name):
    if name.lower().find('py') != -1:
        return name
    else:
        return 'python-%s' % name
