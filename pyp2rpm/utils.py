import functools
import logging
import os
import subprocess
import sys
import re
import copy
import itertools

from pyp2rpm import settings


logger = logging.getLogger(__name__)

PY3 = sys.version > '3'

if PY3:
    str_classes = (str, bytes)
else:
    str_classes = (str, unicode)


class ChangeDir(object):
    """Class to store current directory change cwd to new_path
    and return to previous path at exit, must be run using with statement.
    """

    def __init__(self, new_path):
        self.primary_path = os.getcwd()
        self.new_path = new_path

    def __enter__(self):
        os.chdir(self.new_path)
        return self

    def __exit__(self, type, value, traceback):  # TODO handle exception
        os.chdir(self.primary_path)


class RedirectStdStreams(object):
    """Temporarily redirect stdout/stderr"""

    def __init__(self, stdout=None, stderr=None):
        if settings.CONSOLE_LOGGING:
            self.enabled = False
        else:
            self.enabled = True
            if isinstance(stdout, str):
                stdout = self.stdout_descriptor = open(stdout, "w")
            if isinstance(stderr, str):
                stderr = self.stdout_descriptor = open(stderr, "w")

            self._stdout = stdout or sys.stdout
            self._stderr = stderr or sys.stderr

    def __enter__(self):
        if self.enabled:
            self.old_stdout, self.old_stderr = sys.stdout, sys.stderr
            self.old_stdout.flush()
            self.old_stderr.flush()
            sys.stdout, sys.stderr = self._stdout, self._stderr

    def __exit__(self, exc_type, exc_value, traceback):
        if self.enabled:
            self._stdout.flush()
            self._stderr.flush()
            sys.stdout = self.old_stdout
            sys.stderr = self.old_stderr
            if hasattr(self, 'stdout_descriptor'):
                self.stdout_descriptor.close()
            if hasattr(self, 'stderr_descriptor'):
                self.stderr_descriptor.close()


def memoize_by_args(func):
    """Memoizes return value of a func based on args."""
    memory = {}

    @functools.wraps(func)
    def memoized(*args):
        if args not in memory.keys():
            value = func(*args)
            memory[args] = value

        return memory[args]

    return memoized


def license_from_trove(trove):
    """Finds out license from list of trove classifiers.
    Args:
        trove: list of trove classifiers
    Returns:
        Fedora name of the package license or empty string, if no licensing
        information is found in trove classifiers.
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


def versions_from_trove(trove):
    """Finds out python version from list of trove classifiers.
    Args:
        trove: list of trove classifiers
    Returns:
        python version string
    """
    versions = set()
    for classifier in trove:
        if 'Programming Language :: Python ::' in classifier:
            ver = classifier.split('::')[-1]
            major = ver.split('.')[0].strip()
            if major:
                versions.add(major)
    return sorted([v for v in versions if v.replace('.', '', 1).isdigit()])


def build_srpm(specfile, save_dir):
    """Builds a srpm from given specfile using rpmbuild.
    Generated srpm is stored in directory specified by save_dir.

    Args:
        specfile: path to a specfile
        save_dir: path to source and build tree
    """
    logger.info('Starting rpmbuild to build: {0} SRPM.'.format(specfile))
    if save_dir != settings.DEFAULT_PKG_SAVE_PATH:
        try:
            msg = subprocess.Popen(['rpmbuild',
                                    '--define', '_sourcedir {0}'.format(save_dir),
                                    '--define', '_builddir {0}'.format(save_dir),
                                    '--define', '_srcrpmdir {0}'.format(save_dir),
                                    '--define', '_rpmdir {0}'.format(save_dir),
                                    '-bs', specfile], stdout=subprocess.PIPE).communicate()[0].strip()
        except OSError:
            logger.error('Rpmbuild failed for specfile: {0} and save_dir: {1}'.format(
                specfile, save_dir), exc_info=True)
            msg = 'Rpmbuild failed. See log for more info.'
        return msg
    else:
        if not os.path.exists(save_dir):
            raise IOError('Specify folder to store a file (SAVE_DIR) or install rpmdevtools.')
        try:
            msg = subprocess.Popen(['rpmbuild',
                                    '--define', '_sourcedir {0}'.format(save_dir + '/SOURCES'),
                                    '--define', '_builddir {0}'.format(save_dir + '/BUILD'),
                                    '--define', '_srcrpmdir {0}'.format(save_dir + '/SRPMS'),
                                    '--define', '_rpmdir {0}'.format(save_dir + '/RPMS'),
                                    '-bs', specfile], stdout=subprocess.PIPE).communicate()[0].strip()
        except OSError:
            logger.error('Rpmbuild failed for specfile: {0} and save_dir: {1}'.format(
                specfile, save_dir), exc_info=True)
            msg = 'Rpmbuild failed. See log for more info.'
        return msg


def remove_major_minor_suffix(scripts):
    """Checks if executables already contain a "-MAJOR.MINOR" suffix. """
    minor_major_regex = re.compile("-\d.?\d?$")
    return set([x for x in scripts if not minor_major_regex.search(x)])


def runtime_to_build(runtime_deps):
    """Adds all runtime deps to build deps"""
    build_deps = copy.deepcopy(runtime_deps)
    for dep in build_deps:
        if len(dep) > 0:
            dep[0] = 'BuildRequires'
    return build_deps


def unique_deps(deps):
    """Remove duplicities from deps list of the lists"""
    deps.sort()
    return list(k for k, _ in itertools.groupby(deps))


def get_interpreter_path(current=True):
    """Returns expected path to current python interpreter."""
    if current:
        return sys.executable
    else:
        interpreter = settings.PYTHON_INTERPRETER
        version = '3' if sys.version == '2' else '2'
        return interpreter + version


if PY3:
    def console_to_str(s):
        try:
            return s.decode(sys.__stdout__.encoding)
        except UnicodeDecodeError:
            return s.decode('utf-8')
else:
    def console_to_str(s):
        return s
