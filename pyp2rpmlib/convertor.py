import functools
import os
import xmlrpclib

import jinja2

from pyp2rpmlib import exceptions
from pyp2rpmlib import metadata_extractors
from pyp2rpmlib import package_data
from pyp2rpmlib import package_getters
from pyp2rpmlib import settings

class Convertor(object):
    def __init__(self, name = None, version = None, save_dir = None, source_from = 'pypi', metadata_from = 'pypi', template = 'fedora'):
        self.name = name
        self.version = version
        self.save_dir = save_dir
        self.source_from = source_from
        self.metadata_from = metadata_from
        self.template = template

        self._getter = None
        self._metadata_extractor = None
        self._client = None
        self._client_set = False

    def convert(self):
        # move file into position
        local_file = self.getter().get()

        # save name and version from the file (rewrite if set previously)
        self.name, self.version = self.getter().get_name_version()

        data = self.metadata_extractor(local_file).extract_data()
        jinja_env = jinja2.Environment(loader = jinja2.PackageLoader('pyp2rpmlib', 'templates'))
        jinja_template = jinja_env.get_template('%s.spec' % self.template)

        return jinja_template.render(data = data)

    def getter(self):
        if not self._getter:
            if self.source_from == 'pypi':
                if self.name == None: raise exceptions.NameNotSpecifiedException('Must specify package when getting from PyPI.')
                self._getter = package_getters.Downloader(self.client, self.name, self.version, self.save_dir)
            elif os.path.exists(source_from):
                self._getter = package_getters.LocalData(self.source_from, self.save_dir)
            else:
                raise OSError('"%s" is neither one of preset sources nor a file.' % self.source_from)

        return self._getter

    def metadata_extractor(self, local_file):
        if not self._metadata_extractor:
            if self.metadata_from == 'pypi':
                self._metadata_extractor = metadata_extractors.PypiMetadataExtractor(local_file, self.name, self.version, self.client)
            else:
                self_.metadata_extractor = metadata_extractors.LocalMetadataExtractor(local_file, self.name, self.version)

        return self._metadata_extractor

    @property
    def client(self):
        # cannot use "if self._client"...
        if not self._client_set:
            self._client = xmlrpclib.ServerProxy(settings.PYPI_URL)
            self._client_set = True

        return self._client
