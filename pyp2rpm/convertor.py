import logging
import os
import sys
import xmlrpc

import jinja2

from pyp2rpm import exceptions
from pyp2rpm import filters
from pyp2rpm import metadata_extractors
from pyp2rpm import name_convertor
from pyp2rpm import package_getters
from pyp2rpm import settings

logger = logging.getLogger(__name__)


class Convertor():
    """Object that takes care of the actual process of converting the package."""

    def __init__(self, name=None, version=None,
                 save_dir=settings.DEFAULT_PKG_SAVE_PATH,
                 template=settings.DEFAULT_TEMPLATE,
                 distro=settings.DEFAULT_DISTRO,
                 source_from=settings.DEFAULT_PKG_SOURCE,
                 metadata_from=settings.DEFAULT_METADATA_SOURCE,
                 base_python_version=settings.DEFAULT_PYTHON_VERSION,
                 python_versions=[],
                 rpm_name=None):
        self.name = name
        self.version = version
        self.save_dir = save_dir
        self.source_from = source_from
        self.metadata_from = metadata_from
        self.base_python_version = base_python_version
        self.python_versions = python_versions
        self.template = template
        self.name_convertor = name_convertor.NameConvertor(distro)
        if not self.template.endswith('.spec'):
            self.template = '{0}.spec'.format(self.template)
        self.rpm_name = rpm_name

    def convert(self):
        """Returns RPM SPECFILE.
        Returns:
            Rendered RPM SPECFILE.
        """
        # move file into position
        try:
            local_file = self.getter.get()
        except (exceptions.NoSuchPackageException, OSError) as e:
            logger.error(
                'Failed and exiting:', exc_info=True)
            logger.info("That's all folks!")
            sys.exit(e)

        # save name and version from the file (rewrite if set previously)
        self.name, self.version = self.getter.get_name_version()

        self.local_file = local_file
        data = self.metadata_extractor.extract_data()
        data.base_python_version = self.base_python_version
        data.python_versions = self.python_versions
        jinja_env = jinja2.Environment(loader=jinja2.ChoiceLoader([
            jinja2.FileSystemLoader(['/']),
            jinja2.PackageLoader('pyp2rpm', 'templates'), ])
        )

        for filter in filters.__all__:
            jinja_env.filters[filter.__name__] = filter

        try:
            jinja_template = jinja_env.get_template(
                os.path.abspath(self.template))
        except jinja2.exceptions.TemplateNotFound:
            # absolute path not found => search in default template dir
            logger.info('Template: {0} was not found in {1} using default template dir'.format(
                self.template, os.path.abspath(self.template)))
            jinja_template = jinja_env.get_template(self.template)

        return jinja_template.render(data=data, name_convertor=name_convertor)

    @property
    def getter(self):
        """Returns an instance of proper PackageGetter subclass. Always returns the same instance.

        Returns:
            Instance of the proper PackageGetter subclass according to self.source_from.
        Raises:
            NoSuchSourceException if source to get the package from is unknown
            NoSuchPackageException if the package is unknown on PyPI
        """
        if not hasattr(self, '_getter'):
            if self.source_from == 'pypi':
                if self.name is None:
                    raise exceptions.NameNotSpecifiedException(
                        'Must specify package when getting from PyPI.')
                    logger.error(
                        'Name of the package was not specified', exc_info=True)
                    logger.info("That's all folks!")
                self._getter = package_getters.PypiDownloader(
                    self.client,
                    self.name,
                    self.version,
                    self.save_dir)
            elif os.path.exists(self.source_from):
                self._getter = package_getters.LocalFileGetter(
                    self.source_from,
                    self.save_dir)
            else:
                raise exceptions.NoSuchSourceException(
                    '"{0}" is neither one of preset sources nor a file.'.format(self.source_from))
                logger.error(
                    '{0} is neither one of preset sources nor a file.'.format(self.source_from), exc_info=True)
                logger.info("That's all folks!")

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
    def metadata_extractor(self):
        """Returns an instance of proper MetadataExtractor subclass. Always returns the same instance.

        Returns:
            The proper MetadataExtractor subclass according to self.metadata_from.
        """
        if not hasattr(self, '_local_file'):
            raise AttributeError(
                'local_file attribute must be set before calling metadata_extractor')

        if not hasattr(self, '_metadata_extractor'):
            if self.metadata_from == 'pypi':
                logger.info('Getting metadata from pypi')
                self._metadata_extractor = metadata_extractors.PypiMetadataExtractor(
                    self.local_file,
                    self.name,
                    self.name_convertor,
                    self.version,
                    self.client,
                    self.rpm_name)
            else:
                logger.info('Getting metadata from local file')
                self._metadata_extractor = metadata_extractors.LocalMetadataExtractor(
                    self.local_file,
                    self.name,
                    self.name_convertor,
                    self.version,
                    self.rpm_name)

        return self._metadata_extractor

    @property
    def client(self):
        """Returns the XMLRPC client for PyPI. Always returns the same instance.

        Returns:
            XMLRPC client for PyPI.
        """
        # cannot use "if self._client"...
        if not hasattr(self, '_client'):
            if self.source_from == 'pypi':
                self._client = xmlrpc.client.ServerProxy(settings.PYPI_URL)
                self._client_set = True
            else:
                self._client = None

        return self._client
