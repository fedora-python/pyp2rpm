import functools
import logging
import os
import subprocess
import sys

from pyp2rpm import settings


logger = logging.getLogger(__name__)

PY3 = sys.version > '3'

if PY3:
    str_classes = (str, bytes)
else:
    str_classes = (str, unicode)


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
            logger.error('Rpmbuild failed for specfile: {0} and save_dir: {1}'.format(specfile, save_dir), exc_info=True)
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
            logger.error('Rpmbuild failed for specfile: {0} and save_dir: {1}'.format(specfile, save_dir), exc_info=True)
            msg = 'Rpmbuild failed. See log for more info.'
        return msg
