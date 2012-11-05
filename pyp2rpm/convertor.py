import os
import sys
try:
    import xmlrpclib
except ImportError:
    import xmlrpc.client as xmlrpclib

import jinja2

from pyp2rpm import exceptions
from pyp2rpm import filters
from pyp2rpm import metadata_extractors
from pyp2rpm import name_convertor
from pyp2rpm import package_data
from pyp2rpm import package_getters
from pyp2rpm import settings

class Convertor(object):
    """Object that takes care of the actual process of converting the package."""
    def __init__(self, name = None, version = None,
                 save_dir = settings.DEFAULT_PKG_SAVE_PATH,
                 template = settings.DEFAULT_TEMPLATE,
                 distro = settings.DEFAULT_DISTRO,
                 source_from = settings.DEFAULT_PKG_SOURCE,
                 metadata_from = settings.DEFAULT_METADATA_SOURCE,
                 base_python_version = settings.DEFAULT_PYTHON_VERSION,
                 python_versions = []):
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

        self._getter = None
        self._metadata_extractor = None
        self._client = None
        self._client_set = False

    def convert(self):
        """Returns RPM SPECFILE.
        Returns:
            Rendered RPM SPECFILE.
        """
        # move file into position
        try:
            local_file = self.getter.get()
        except (exceptions.NoSuchPackageException, OSError) as e:
            sys.exit(e)

        # save name and version from the file (rewrite if set previously)
        self.name, self.version = self.getter.get_name_version()

        data = self.get_metadata_extractor(local_file).extract_data()
        data.base_python_version = self.base_python_version
        data.python_versions = self.python_versions
        jinja_env = jinja2.Environment(loader = jinja2.ChoiceLoader([
                                                    jinja2.FileSystemLoader(['/']),
                                                    jinja2.PackageLoader('pyp2rpm', 'templates'),
                                                ])
                                      )
        for filter in filters.__all__:
            jinja_env.filters[filter.__name__] = filter

        try:
            jinja_template = jinja_env.get_template(os.path.abspath(self.template))
        except jinja2.exceptions.TemplateNotFound: # absolute path not found => search in default template dir
            jinja_template = jinja_env.get_template(self.template)

        return jinja_template.render(data = data, name_convertor = name_convertor)

    @property
    def getter(self):
        """Returns the proper PackageGetter subclass.
        Returns:
            The proper PackageGetter subclass according to self.source_from.
        Raises:
            NoSuchSourceException if source to get the package from is unknown
            NoSuchPackageException if the package is unknown on PyPI
        """
        if not self._getter:
            if self.source_from == 'pypi':
                if self.name == None: raise exceptions.NameNotSpecifiedException('Must specify package when getting from PyPI.')
                self._getter = package_getters.PypiDownloader(self.client,
                                                              self.name,
                                                              self.version,
                                                              self.save_dir)
            elif os.path.exists(self.source_from):
                self._getter = package_getters.LocalFileGetter(self.source_from,
                                                               self.save_dir)
            else:
                raise exceptions.NoSuchSourceException('"{0}" is neither one of preset sources nor a file.'.format(self.source_from))

        return self._getter

    def get_metadata_extractor(self, local_file):
        """Returns the proper MetadataExtractor subclass.
        Returns:
            The proper MetadataExtractor subclass according to self.metadata_from.
        """
        if not self._metadata_extractor:
            if self.metadata_from == 'pypi':
                self._metadata_extractor = metadata_extractors.PypiMetadataExtractor(local_file,
                                                                                     self.name,
                                                                                     self.name_convertor,
                                                                                     self.version,
                                                                                     self.client)
            else:
                self._metadata_extractor = metadata_extractors.LocalMetadataExtractor(local_file,
                                                                                      self.name,
                                                                                      self.name_convertor,
                                                                                      self.version)

        return self._metadata_extractor

    @property
    def client(self):
        """Returns the XMLRPC client for PyPI.
        Returns:
            XMLRPC client for PyPI.
        """
        # cannot use "if self._client"...
        if not self._client_set:
            self._client = xmlrpclib.ServerProxy(settings.PYPI_URL)
            self._client_set = True

        return self._client
