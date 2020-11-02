import logging
import os
import re
import sys
try:
    import urllib2 as urllib
    from urllib2 import urlopen, HTTPError, URLError
except ImportError:
    import urllib
    from urllib import request
    from urllib.request import urlopen, HTTPError, URLError
    urllib.Request = request.Request
    urllib.ProxyHandler = request.ProxyHandler
    urllib.build_opener = request.build_opener
    urllib.install_opener = request.install_opener
import json

try:
    import dnf
except ImportError:
    dnf = None

import jinja2
import pprint

from pyp2rpm import exceptions
from pyp2rpm import filters
from pyp2rpm import metadata_extractors
from pyp2rpm import name_convertor
from pyp2rpm import package_getters
from pyp2rpm import settings

logger = logging.getLogger(__name__)


class Convertor(object):
    """Object that takes care of the actual process of converting
    the package.
    """

    # PyPI client interface; tests may override this attribute
    _client = None

    def __init__(self, package=None, version=None, prerelease=False,
                 save_dir=None,
                 template=settings.DEFAULT_TEMPLATE,
                 distro=settings.DEFAULT_DISTRO,
                 base_python_version=settings.DEFAULT_PYTHON_VERSION,
                 python_versions=[],
                 rpm_name=None, proxy=None, venv=True, autonc=False):
        self.package = package
        self.version = version
        self.prerelease = prerelease
        self.save_dir = save_dir
        self.base_python_version = base_python_version
        self.python_versions = list(python_versions)
        self.template = template
        self.distro = distro
        if not self.template.endswith('.spec'):
            self.template = '{0}.spec'.format(self.template)
        self.rpm_name = rpm_name
        self.proxy = proxy
        self.venv = venv
        self.autonc = autonc
        self.pypi = True
        suffix = os.path.splitext(self.package)[1]
        if (os.path.exists(self.package)
                and suffix in settings.ARCHIVE_SUFFIXES
                and not os.path.isdir(self.package)):
            self.pypi = False

    @property
    def template_base_py_ver(self):
        """Return default base python version for chosen template. """
        return settings.DEFAULT_PYTHON_VERSIONS[self.distro][0]

    @property
    def template_py_vers(self):
        """Return default python versions for chosen template. """
        return settings.DEFAULT_PYTHON_VERSIONS[self.distro][1:]

    def merge_versions(self, data):
        """Merges python versions specified in command lines options with
        extracted versions, checks if some of the versions is not > 2 if EPEL6
        template will be used. attributes base_python_version and
        python_versions contain values specified by command line options or
        default values, data.python_versions contains extracted data.
        """
        if self.distro == "epel6":
            # if user requested version greater than 2, writes error message
            # and exits
            requested_versions = self.python_versions
            if self.base_python_version:
                requested_versions += [self.base_python_version]
            if any(int(ver[0]) > 2 for ver in requested_versions):
                sys.stderr.write(
                    "Invalid version, major number of python version for "
                    "EPEL6 spec file must not be greater than 2.\n")
                sys.exit(1)
            # if version greater than 2 were extracted it is removed
            data.python_versions = [
                ver for ver in data.python_versions if not int(ver[0]) > 2]

        # Set python versions from default values in settings.
        base_version, additional_versions = (
            self.template_base_py_ver, self.template_py_vers)

        # Sync default values with extracted versions from PyPI classifiers.
        if data.python_versions:
            if base_version not in data.python_versions:
                base_version = data.python_versions[0]

            additional_versions = [
                v for v in additional_versions if v in data.python_versions]

        # Override default values with those set from command line if any.
        if self.base_python_version:
            base_version = self.base_python_version
        if self.python_versions:
            additional_versions = self.python_versions
        # Ensure there are no duplicate versions
        additional_versions = [
            v for v in additional_versions if v != base_version]

        data.base_python_version = base_version
        data.python_versions = additional_versions

    def convert(self):
        """Returns RPM SPECFILE.
        Returns:
            rendered RPM SPECFILE.
        """
        # move file into position
        try:
            local_file = self.getter.get()
        except (exceptions.NoSuchPackageException, OSError) as e:
            logger.error(
                "Failed and exiting:", exc_info=True)
            logger.info("Pyp2rpm failed. See log for more info.")

            sys.exit(e)

        # save name and version from the file (rewrite if set previously)
        self.name, self.version = self.getter.get_name_version()

        self.local_file = local_file
        data = self.metadata_extractor.extract_data(self.client)
        logger.debug("Extracted metadata:")
        logger.debug(pprint.pformat(data.data))
        self.merge_versions(data)

        jinja_env = jinja2.Environment(loader=jinja2.ChoiceLoader([
            jinja2.FileSystemLoader(['/']),
            jinja2.PackageLoader('pyp2rpm', 'templates'), ]))

        for filter in filters.__all__:
            jinja_env.filters[filter.__name__] = filter

        try:
            jinja_template = jinja_env.get_template(
                os.path.abspath(self.template))
        except jinja2.exceptions.TemplateNotFound:
            # absolute path not found => search in default template dir
            logger.warning('Template: {0} was not found in {1} using default '
                           'template dir.'.format(
                               self.template, os.path.abspath(self.template)))

            jinja_template = jinja_env.get_template(self.template)
            logger.info('Using default template: {0}.'.format(self.template))

        ret = jinja_template.render(data=data, name_convertor=name_convertor)
        return re.sub(r'[ \t]+\n', "\n", ret)

    @property
    def getter(self):
        """Returns an instance of proper PackageGetter subclass. Always
        returns the same instance.

        Returns:
            Instance of the proper PackageGetter subclass according to
            provided argument.
        Raises:
            NoSuchSourceException if source to get the package from is unknown
            NoSuchPackageException if the package is unknown on PyPI
        """
        if not hasattr(self, '_getter'):
            if not self.pypi:
                self._getter = package_getters.LocalFileGetter(
                    self.package,
                    self.save_dir)
            else:
                logger.debug(
                    '{0} does not exist as local file trying PyPI.'.format(
                        self.package))
                self._getter = package_getters.PypiDownloader(
                    self.client,
                    self.package,
                    self.version,
                    self.prerelease,
                    self.save_dir)

        return self._getter

    @property
    def local_file(self):
        """Returns an local_file attribute needed for metadata_extractor.

        *Must* be set before calling metadata_extractor attribute.

        Returns:
            Full path of local/downloaded file
        """
        return self._local_file

    @local_file.setter
    def local_file(self, value):
        """Setter for local_file attribute
        """
        self._local_file = value

    @property
    def name_convertor(self):
        if not hasattr(self, '_name_convertor'):
            name_convertor.NameConvertor.distro = self.distro
            if self.autonc or (self.autonc is None and
                (self.distro == 'fedora' or
                 self.distro == 'mageia')):
                logger.debug("Using AutoProvidesNameConvertor to convert "
                             "names of the packages.")
                self._name_convertor = name_convertor.AutoProvidesNameConvertor(
                    self.distro)
            elif dnf is None:
                logger.warning("Dnf module not found, please dnf install "
                               "python{0}-dnf to improve accuracy of name "
                               "conversion.".format(sys.version[0]))
                logger.debug(
                    "Using NameConvertor to convert names of the packages.")
                self._name_convertor = name_convertor.NameConvertor(
                    self.distro)
            else:
                logger.debug("Using DandifiedNameConvertor to convert names "
                             "of the packages.")
                self._name_convertor = name_convertor.DandifiedNameConvertor(
                    self.distro)
        return self._name_convertor

    @property
    def metadata_extractor(self):
        """Returns an instance of proper MetadataExtractor subclass.
        Always returns the same instance.

        Returns:
            The proper MetadataExtractor subclass according to local file
            suffix.
        """
        if not hasattr(self, '_local_file'):
            raise AttributeError("local_file attribute must be set before "
                                 "calling metadata_extractor")
        if not hasattr(self, '_metadata_extractor'):
            if self.local_file.endswith('.whl'):
                logger.info("Getting metadata from wheel using "
                            "WheelMetadataExtractor.")
                extractor_cls = metadata_extractors.WheelMetadataExtractor
            else:
                logger.info("Getting metadata from setup.py using "
                            "SetupPyMetadataExtractor.")
                extractor_cls = metadata_extractors.SetupPyMetadataExtractor

            base_python_version = (
                self.base_python_version or self.template_base_py_ver)

            self._metadata_extractor = extractor_cls(
                self.local_file,
                self.name,
                self.name_convertor,
                self.version,
                self.rpm_name,
                self.venv,
                self.distro,
                base_python_version)

        return self._metadata_extractor

    @property
    def client(self):
        """JSON client for PyPI. Always returns the same instance.

        If the package is provided as a path to compressed source file,
        PyPI will not be used and the client will not be instantiated.

        Returns:
            JSON client for PyPI or None.
        """
        if self._client is None and self.pypi:
            self._client = PyPIClient(proxy=self.proxy)
            self._client_set = True

        return self._client


class PyPIClient():
    """This class interfaces with the PyPI JSON API."""

    no_such_package = {'info': {}, 'urls': [], 'releases': {}}

    def __init__(self, proxy=None):
        self.cache = {}
        if proxy:
            proxyhandler = urllib.ProxyHandler({"http": proxy})
            opener = urllib.build_opener(proxyhandler)
            urllib.install_opener(opener)
            logger.info('Using provided proxy: {0}.'.format(proxy))

    def get_json(self, name, version):
        if (name, version) in self.cache:
            return self.cache[(name, version)]
        if version:
            url = "{0}/{1}/{2}/json".format(settings.PYPI_URL, name, version)
        else:
            url = "{0}/{1}/json".format(settings.PYPI_URL, name)
        try:
            json_info = urlopen(url)
        except HTTPError as e:
            self.cache[(name, version)] = self.no_such_package
            return self.cache[(name, version)]
        except URLError as e:
            sys.stderr.write("Failed to connect to server: {0} \n".format(e))
            raise SystemExit(3)
        self.cache[(name, version)] = json.loads(json_info.read().decode("utf-8"))
        return self.cache[(name, version)]

    def release_data(self, name, version):
        return self.get_json(name, version)['info']

    def release_urls(self, name, version):
        return self.get_json(name, version)['urls']

    def package_releases(self, name, show_hidden):
        return self.get_json(name, None)['releases'].keys()
