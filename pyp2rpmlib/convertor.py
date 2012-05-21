import os
import sys
import xmlrpclib

import jinja2

from pyp2rpmlib import exceptions
from pyp2rpmlib import filters
from pyp2rpmlib import metadata_extractors
from pyp2rpmlib import package_data
from pyp2rpmlib import package_getters
from pyp2rpmlib import settings

class Convertor(object):
    """Object that takes care of the actual process of converting the package."""
    def __init__(self, name = None, version = None,
                 save_dir = settings.DEFAULT_PKG_SAVE_PATH,
                 template = settings.DEFAULT_TEMPLATE,
                 source_from = settings.DEFAULT_PKG_SOURCE,
                 metadata_from = settings.DEFAULT_METADATA_SOURCE,
                 python_versions = []):
        self.name = name
        self.version = version
        self.save_dir = save_dir
        self.source_from = source_from
        self.metadata_from = metadata_from
        self.template = template
        self.python_versions = python_versions

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
            local_file = self.getter().get()
        except (exceptions.NoSuchPackageException, OSError) as e:
            sys.exit(e)

        # save name and version from the file (rewrite if set previously)
        self.name, self.version = self.getter().get_name_version()

        data = self.metadata_extractor(local_file).extract_data()
        data.python_versions = self.python_versions
        jinja_env = jinja2.Environment(loader = jinja2.PackageLoader('pyp2rpmlib', 'templates'))
        for filter in filters.__all__:
            jinja_env.filters[filter.__name__] = filter
        jinja_template = jinja_env.get_template('%s.spec' % self.template)

        return jinja_template.render(data = data)

    def getter(self):
        """Returns the proper PackageGetter subclass.
        Returns:
            The proper PackageGetter subclass according to self.source_from.
        """
        if not self._getter:
            if self.source_from == 'pypi':
                if self.name == None: raise exceptions.NameNotSpecifiedException('Must specify package when getting from PyPI.')
                self._getter = package_getters.PypiDownloader(self.client, self.name, self.version, self.save_dir)
            elif os.path.exists(self.source_from):
                self._getter = package_getters.LocalFileGetter(self.source_from, self.save_dir)
            else:
                raise OSError('"%s" is neither one of preset sources nor a file.' % self.source_from)

        return self._getter

    def metadata_extractor(self, local_file):
        """Returns the proper MetadataExtractor subclass.
        Returns:
            The proper MetadataExtractor subclass according to self.metadata_from.
        """
        if not self._metadata_extractor:
            if self.metadata_from == 'pypi':
                self._metadata_extractor = metadata_extractors.PypiMetadataExtractor(local_file, self.name, self.version, self.client)
            else:
                self._metadata_extractor = metadata_extractors.LocalMetadataExtractor(local_file, self.name, self.version)

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
