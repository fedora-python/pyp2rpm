import logging
import os
import sys
try:
    import urllib2 as urllib
except ImportError:
    import urllib
    from urllib import request
    urllib.Request = request.Request
    urllib.ProxyHandler = request.ProxyHandler
    urllib.build_opener = request.build_opener
    urllib.install_opener = request.install_opener
try:
    import xmlrpclib
except ImportError:
    import xmlrpc.client as xmlrpclib

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
    """Object that takes care of the actual process of converting the package."""

    def __init__(self, package=None, version=None,
                 save_dir=None,
                 template=settings.DEFAULT_TEMPLATE,
                 distro=settings.DEFAULT_DISTRO,
                 base_python_version=settings.DEFAULT_PYTHON_VERSION,
                 python_versions=[],
                 rpm_name=None, proxy=None, venv=True):
        self.package = package
        self.version = version
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
        self.pypi = True
        suffix = os.path.splitext(self.package)[1]
        if os.path.exists(self.package) and suffix in settings.ARCHIVE_SUFFIXES\
                and not os.path.isdir(self.package):
            self.pypi = False

    def merge_versions(self, data):
        """Merges python versions specified in command lines options with
        extracted versions, checks if some of the versions is not > 2 if EPEL6 template
        will be used. attributes base_python_version and python_versions contain
        values specified by command line options or default values, 
        data.base_python_version and data.python_versions contain extracted data.
        """
        if self.template == "epel6.spec":
            # if user requested version greater than 2, writes error message and exits
            if (any(int(ver[0]) > 2 for ver in self.python_versions
                    + ([self.base_python_version] if self.base_python_version else [])
                    + [data.base_python_version])):
                sys.stderr.write("Invalid version, major number of python version for EPEL6 "
                                 "spec file must not be greater than 2.\n".format(self.base_python_version))
                sys.exit(1)
            # if version greater than 2 were extracted it is removed
            data.python_versions = [ver for ver in data.python_versions if not int(ver[0]) > 2]

        if self.base_python_version or self.python_versions:
            data.base_python_version = self.base_python_version
            data.python_versions = [v for v in self.python_versions
                                    if not v == data.base_python_version]
        elif data.base_python_version in data.python_versions:
            data.python_versions.remove(data.base_python_version)

    def convert(self):
        """Returns RPM SPECFILE.
        Returns:
            endered RPM SPECFILE.
        """
        # move file into position
        try:
            local_file = self.getter.get()
        except (exceptions.NoSuchPackageException, OSError) as e:
            logger.error(
                'Failed and exiting:', exc_info=True)
            logger.info('Pyp2rpm failed. See log for more info.')

            sys.exit(e)

        # save name and version from the file (rewrite if set previously)
        self.name, self.version = self.getter.get_name_version()

        self.local_file = local_file
        data = self.metadata_extractor.extract_data(self.client)
        logger.debug('Extracted metadata:')
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
            logger.warn('Template: {0} was not found in {1} using default template dir.'.format(
                self.template, os.path.abspath(self.template)))

            jinja_template = jinja_env.get_template(self.template)
            logger.info('Using default template: {0}.'.format(self.template))

        return jinja_template.render(data=data, name_convertor=name_convertor)

    @property
    def getter(self):
        """Returns an instance of proper PackageGetter subclass. Always returns the same instance.

        Returns:
            Instance of the proper PackageGetter subclass according to provided argument.
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
                logger.debug('{0} doesnt exists as local file trying PyPI.'.format(self.package))
                self._getter = package_getters.PypiDownloader(
                    self.client,
                    self.package,
                    self.version,
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
            if dnf is None:
                logger.warn("Dnf module not found, please dnf install python{0}-dnf "
                        "to improve accuracy of name conversion.".format(sys.version[0]))
                logger.debug("Using NameConvertor to convert names of the packages.")
                self._name_convertor = name_convertor.NameConvertor(self.distro)
            else:
                logger.debug("Using DandifiedNameConvertor to convert names of the packages.")
                self._name_convertor = name_convertor.DandifiedNameConvertor(self.distro)
        return self._name_convertor

    @property
    def metadata_extractor(self):
        """Returns an instance of proper MetadataExtractor subclass. 
        Always returns the same instance.

        Returns:
            The proper MetadataExtractor subclass according to local file suffix.
        """
        if not hasattr(self, '_local_file'):
            raise AttributeError(
                'local_file attribute must be set before calling metadata_extractor')
        if not hasattr(self, '_metadata_extractor'):
            if self.local_file.endswith('.whl'):
                logger.info('Getting metadata from wheel using WheelMetadataExtractor.')
                extractor_cls = metadata_extractors.WheelMetadataExtractor
            else:
                logger.info('Getting metadata from setup.py using SetupPyMetadataExtractor.')
                extractor_cls = metadata_extractors.SetupPyMetadataExtractor

            self._metadata_extractor = extractor_cls(
                self.local_file,
                self.name,
                self.name_convertor,
                self.version,
                self.rpm_name,
                self.venv,
                self.base_python_version)

        return self._metadata_extractor

    @property
    def client(self):
        """Returns the XMLRPC client for PyPI. Always returns the same instance.

        Returns:
            XMLRPC client for PyPI.
        """
        # cannot use "if self._client"...
        if self.proxy:
            proxyhandler = urllib.ProxyHandler({"http": self.proxy})
            opener = urllib.build_opener(proxyhandler)
            urllib.install_opener(opener)
            transport = ProxyTransport()
        if not hasattr(self, '_client'):
            transport = None
            if self.pypi:
                if self.proxy:
                    logger.info('Using provided proxy: {0}.'.format(self.proxy))
                self._client = xmlrpclib.ServerProxy(settings.PYPI_URL, transport=transport)
                self._client_set = True
            else:
                self._client = None

        return self._client


class ProxyTransport(xmlrpclib.Transport):
    """This class serves as Proxy Transport for XMLRPC server."""

    def request(self, host, handler, request_body, verbose):
        self.verbose = verbose
        url = 'http://{0}{1}'.format(host, handler)
        request = urllib.Request(url)
        request.add_data(request_body)
        request.add_header("User-Agent", self.user_agent)
        request.add_header("Content-Type", "text/html")
        f = urllib.urlopen(request)
        return self.parse_response(f)
