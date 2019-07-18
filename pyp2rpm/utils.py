import contextlib
import functools
import locale
import logging
import os
import subprocess
import sys
import re
import copy
import itertools

try:
    import rpm
except ImportError:
    rpm = None

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


def build_srpm(specfile, save_dir):
    """Builds a srpm from given specfile using rpmbuild.
    Generated srpm is stored in directory specified by save_dir.

    Args:
        specfile: path to a specfile
        save_dir: path to source and build tree
    """
    logger.info('Starting rpmbuild to build: {0} SRPM.'.format(specfile))
    if save_dir != get_default_save_path():
        try:
            msg = subprocess.Popen(
                ['rpmbuild',
                 '--define', '_sourcedir {0}'.format(save_dir),
                 '--define', '_builddir {0}'.format(save_dir),
                 '--define', '_srcrpmdir {0}'.format(save_dir),
                 '--define', '_rpmdir {0}'.format(save_dir),
                 '-bs', specfile], stdout=subprocess.PIPE).communicate(
                 )[0].strip()
        except OSError:
            logger.error(
                "Rpmbuild failed for specfile: {0} and save_dir: {1}".format(
                    specfile, save_dir), exc_info=True)
            msg = 'Rpmbuild failed. See log for more info.'
        return msg
    else:
        if not os.path.exists(save_dir):
            raise IOError("Specify folder to store a file (SAVE_DIR) "
                          "or install rpmdevtools.")
        try:
            msg = subprocess.Popen(
                ['rpmbuild',
                 '--define', '_sourcedir {0}'.format(save_dir + '/SOURCES'),
                 '--define', '_builddir {0}'.format(save_dir + '/BUILD'),
                 '--define', '_srcrpmdir {0}'.format(save_dir + '/SRPMS'),
                 '--define', '_rpmdir {0}'.format(save_dir + '/RPMS'),
                 '-bs', specfile], stdout=subprocess.PIPE).communicate(
                )[0].strip()
        except OSError:
            logger.error("Rpmbuild failed for specfile: {0} and save_dir: "
                         "{1}".format(specfile, save_dir), exc_info=True)
            msg = 'Rpmbuild failed. See log for more info.'
        return msg


def remove_major_minor_suffix(scripts):
    """Checks if executables already contain a "-MAJOR.MINOR" suffix. """
    minor_major_regex = re.compile(r"-\d.?\d?$")
    return [x for x in scripts if not minor_major_regex.search(x)]


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


if PY3:
    def console_to_str(s):
        try:
            return s.decode(sys.__stdout__.encoding)
        except UnicodeDecodeError:
            return s.decode('utf-8')
else:
    def console_to_str(s):
        return s


@contextlib.contextmanager
def c_time_locale():
    """Context manager with C LC_TIME locale"""
    old_time_locale = locale.getlocale(locale.LC_TIME)
    locale.setlocale(locale.LC_TIME, 'C')
    yield
    try:
        locale.setlocale(locale.LC_TIME, old_time_locale)
    except locale.Error:
        # https://bugs.python.org/issue30755
        # Python may alias the configured locale to another name, and
        # that locale may not be installed.  In this case, the locale
        # should simply be left in the 'C' locale.
        pass


def rpm_eval(macro):
    """Get value of given macro using rpm tool"""
    try:
        value = subprocess.Popen(
            ['rpm', '--eval', macro],
            stdout=subprocess.PIPE).communicate()[0].strip()
    except OSError:
        logger.error('Failed to get value of {0} rpm macro'.format(
            macro), exc_info=True)
        value = b''
    return console_to_str(value)


def get_default_save_path():
    """Return default save path for the packages"""
    macro = '%{_topdir}'
    if rpm:
        save_path = rpm.expandMacro(macro)
    else:
        save_path = rpm_eval(macro)
        if not save_path:
            logger.warning("rpm tools are missing, using default save path "
                           "~/rpmbuild/.")
            save_path = os.path.expanduser('~/rpmbuild')
    return save_path
