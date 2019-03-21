import sys
import json
from distutils.core import Command


class extract_dist(Command):
    """Custom distutils command to extract metadata form setup function."""
    description = ("Assigns self.distribution to class attribute to make "
                   "it accessible from outside a class.")
    user_options = [('stdout', None,
                     'print metadata in json format to stdout')]
    class_metadata = None

    def __init__(self, *args, **kwargs):
        """Metadata dictionary is created, all the metadata attributes,
        that were not found are set to default empty values. Checks of data
        types are performed.
        """
        Command.__init__(self, *args, **kwargs)

        self.metadata = {}

        for attr in ['setup_requires', 'tests_require', 'install_requires',
                     'packages', 'py_modules', 'scripts']:
            self.metadata[attr] = to_list(getattr(self.distribution, attr, []))

        try:
            for k, v in getattr(
                    self.distribution, 'extras_require', {}).items():
                if k in ['test, docs', 'doc', 'dev']:
                    attr = 'setup_requires'
                else:
                    attr = 'install_requires'
                self.metadata[attr] += to_list(v)
        except (AttributeError, ValueError):
            # extras require are skipped in case of wrong data format
            # can't log here, because this file is executed in a subprocess
            pass

        for attr in ['url', 'long_description', 'description', 'license']:
            self.metadata[attr] = to_str(
                getattr(self.distribution.metadata, attr, None))

        self.metadata['classifiers'] = to_list(
            getattr(self.distribution.metadata, 'classifiers', []))

        if isinstance(getattr(self.distribution, "entry_points", None), dict):
            self.metadata['entry_points'] = self.distribution.entry_points
        else:
            self.metadata['entry_points'] = None

        self.metadata['test_suite'] = getattr(
            self.distribution, "test_suite", None) is not None

    def initialize_options(self):
        """Sets default value of the stdout option."""
        self.stdout = False

    def finalize_options(self):
        """Abstract method of Command class have to be overridden."""
        pass

    def run(self):
        """Sends extracted metadata in json format to stdout if stdout
        option is specified, assigns metadata dictionary to class_metadata
        variable otherwise.
        """
        if self.stdout:
            sys.stdout.write("extracted json data:\n" + json.dumps(
                self.metadata, default=to_str) + "\n")
        else:
            extract_dist.class_metadata = self.metadata


def to_list(var):
    """Checks if given value is a list, tries to convert, if it is not."""
    if var is None:
        return []
    if isinstance(var, str):
        var = var.split('\n')
    elif not isinstance(var, list):
        try:
            var = list(var)
        except TypeError:
            raise ValueError("{} cannot be converted to the list.".format(var))
    return var


def to_str(var):
    """Similar to to_list function, but for string attributes."""
    try:
        return str(var)
    except TypeError:
        raise ValueError("{} cannot be converted to string.".format(var))
