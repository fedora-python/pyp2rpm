import logging
import re
try:
    import dnf
except ImportError:
    dnf = None

from pyp2rpm import settings
from pyp2rpm import utils
from pyp2rpm.logger import LoggerWriter


logger = logging.getLogger(__name__)


class NameConvertor(object):

    def __init__(self, distro):
        self.distro = distro
        self.reg_start = re.compile(r'^python(\d*|)-(.*)')
        self.reg_end = re.compile(r'(.*)-(python)(\d*|)$')

    @staticmethod
    def rpm_versioned_name(name, version, default_number=False, epel=False):
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
                if not epel:
                    return 'python-{0}'.format(regexp.search(name).group(2))
            return name

        versioned_name = name
        if version:

            if regexp.search(name):
                versioned_name = re.sub(r'^python(\d*|)-', 'python{0}-'.format(version), name)
            else:
                versioned_name = 'python{0}-{1}'.format(version, name)
            if epel and version != settings.DEFAULT_PYTHON_VERSION:
                versioned_name = versioned_name.replace('{0}'.format(
                    version), '%{{python{0}_pkgversion}}'.format(version))
        return versioned_name

    def rpm_name(self, name, python_version=settings.DEFAULT_PYTHON_VERSION):
        """Returns name of the package coverted to (possibly) correct package 
           name according to Packaging Guidelines.
        Args:
            name: name to convert
            python_version: python version for which to retrieve the name of the package
        Returns:
            Converted name of the package, that should be in line with Fedora Packaging Guidelines.
            If for_python is not None, the returned name is in form python%(version)s-%(name)s
        """
        logger.debug('Converting name: {0} to rpm name, version: {1}.'.format(name, python_version))
        rpmized_name = self.base_name(name)

        rpmized_name = 'python-{0}'.format(rpmized_name)

        if self.distro == 'mageia':
            rpmized_name = rpmized_name.lower()
        logger.debug('Rpmized name of {0}: {1}.'.format(name, rpmized_name))
        return NameConvertor.rpm_versioned_name(rpmized_name, python_version)

    def base_name(self, name):
        """Removes any python prefixes of suffixes from name if present."""
        base_name = name.replace('.', "-")
        # remove python prefix if present
        found_prefix = self.reg_start.search(name)
        if found_prefix:
            base_name = found_prefix.group(2)

        # remove -pythonXY like suffix if present
        found_end = self.reg_end.search(name.lower())
        if found_end:
            base_name = found_end.group(1)

        return base_name


class NameVariants(object):
    """Class to generate variants of python package name and choose
    most likely correct one.
    """

    def __init__(self, name, version, py_init=True):
        self.name = name
        self.version = version
        self.variants = {}
        if py_init:
            self.names_init()
            self.variants_init()

    def find_match(self, name):
        for variant in ['python_ver_name', 'pyver_name', 'name_python_ver', 'raw_name']:
            # iterates over all variants and store name to variants if matches
            if canonical_form(name) == canonical_form(getattr(self, variant)):
                self.variants[variant] = name

    def merge(self, other):
        """Merges object with other NameVariants object, not set values 
        of self.variants are replace by values from other object.
        """
        if not isinstance(other, NameVariants):
            raise TypeError("NameVariants isinstance can be merge with"
                            "other isinstance of the same class")
        for key in self.variants:
            self.variants[key] = self.variants[key] or other.variants[key]

        return self

    def names_init(self):
        self.python_ver_name = 'python{0}-{1}'.format(self.version, self.name)
        self.pyver_name = self.name if self.name.startswith('py') else 'py{0}{1}'.format(
            self.version, self.name)
        self.name_python_ver = '{0}-python{1}'.format(self.name, self.version)
        self.raw_name = self.name

    def variants_init(self):
        self.variants = {'python_ver_name': None,
                         'pyver_name': None,
                         'name_python_ver': None,
                         'raw_name': None}

    @property
    def best_matching(self):
        return (self.variants['python_ver_name'] or
                self.variants['pyver_name'] or
                self.variants['name_python_ver'] or
                self.variants['raw_name'])


class DandifiedNameConvertor(NameConvertor):
    """Name convertor based on DNF API query, checks if converted
    name of the package exists in Fedora repositories. If it doesn't, searches
    for the correct variant of the name.
    """

    def __init__(self, *args):
        super(DandifiedNameConvertor, self).__init__(*args)
        if dnf is None or self.distro != 'fedora':
            raise RuntimeError("DandifiedNameConvertor needs optional require dnf, and "
                               "can be used for Fedora distro only.")
        with dnf.Base() as base:
            RELEASEVER = dnf.rpm.detect_releasever(base.conf.installroot)
            base.conf.substitutions['releasever'] = RELEASEVER
            base.read_all_repos()
            base.fill_sack()
            self.query = base.sack.query()

    def rpm_name(self, name, python_version=None):
        """Checks if name converted using superclass rpm_name_method match name
        of package in the query. Searches for correct name if it doesn't.
        """
        original_name = name
        converted = super(DandifiedNameConvertor, self).rpm_name(name, python_version)
        python_query = self.query.filter(name__substr=['python', 'py', original_name,
                                                       canonical_form(original_name)])
        if converted in [pkg.name for pkg in python_query]:
            logger.debug("Converted name exists")
            return converted

        logger.debug("Converted name not found, searches for correct form")

        not_versioned_name = NameVariants(self.base_name(original_name), '')
        versioned_name = NameVariants(self.base_name(original_name), python_version)

        if self.base_name(original_name).startswith("py"):
            nonpy_name = NameVariants(self.base_name(
                original_name)[2:], python_version)

        for pkg in python_query:
            versioned_name.find_match(pkg.name)
            not_versioned_name.find_match(pkg.name)
            if 'nonpy_name' in locals():
                nonpy_name.find_match(pkg.name)

        if 'nonpy_name' in locals():
            versioned_name = versioned_name.merge(nonpy_name)

        correct_form = versioned_name.merge(not_versioned_name).best_matching
        logger.debug("Most likely correct form of the name {0}.".format(correct_form))
        return correct_form or converted


def canonical_form(name):
    return name.lower().replace('-', '').replace('_', '')
