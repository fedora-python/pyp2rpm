import logging
import re

from pyp2rpm import settings


logger = logging.getLogger(__name__)


class NameConvertor(object):

    def __init__(self, distro):
        self.distro = distro

    @staticmethod
    def rpm_versioned_name(name, version, default_number=False):
        """Properly versions the name.
        For example:
        rpm_versioned_name('python-foo', '26') will return python26-foo
        rpm_versioned_name('pyfoo, '3') will return python3-pyfoo

        If version is same as settings.DEFAULT_PYTHON_VERSION, no change is done.

        Args:
            name: name to version
            version: version or None
        Returns:
            Versioned name or the original name if given version is None.
        """
        regexp = re.compile(r'^python(\d*|)-(.*)')

        if not version or version == settings.DEFAULT_PYTHON_VERSION and not default_number:
            found = regexp.search(name)
            # second check is to avoid renaming of python2-devel to python-devel
            if found and found.group(2) != 'devel':
                return 'python-{0}'.format(regexp.search(name).group(2))
            return name

        versioned_name = name
        if version:

            if regexp.search(name):
                versioned_name = re.sub(r'^python(\d*|)-', 'python{0}-'.format(version), name)
            else:
                versioned_name = 'python{0}-{1}'.format(version, name)

        return versioned_name

    def rpm_name(self, name, python_version=None):
        """Returns name of the package coverted to (possibly) correct package 
           name according to Packaging Guidelines.
        Args:
            name: name to convert
            python_version: python version for which to retrieve the name of the package
        Returns:
            Converted name of the package, that should be in line with Fedora Packaging Guidelines.
            If for_python is not None, the returned name is in form python%(version)s-%(name)s
        """
        logger.debug('Converting name: {0} to rpm name.'.format(name))
        rpmized_name = name

        reg_start = re.compile(r'^python(\d*|)-')

        name = name.replace('.', "-")
        # prefix python before pkg name (only if it's not prefixed already)
        if not reg_start.search(name.lower()):
            rpmized_name = 'python-{0}'.format(name)

        reg_end = re.compile(r'(.*)-(python)(\d*|)$')
        found_end = reg_end.search(name.lower())
        if found_end:  # if package has -pythonXY like sufix convert it to prefix
            rpmized_name = '{0}{1}-{2}'.format('python', found_end.group(3), found_end.group(1))

        if self.distro == 'mageia':
            rpmized_name = rpmized_name.lower()
        logger.debug('Rpmized name of {0}: {1}.'.format(name, rpmized_name))
        return NameConvertor.rpm_versioned_name(rpmized_name, python_version)
