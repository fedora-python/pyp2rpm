import xmlrpclib

from pyp2rpmlib.package_data import PackageData

class MetadataExtractor(object):
    def extract_data(self):
        raise NotImplementedError('Whoops, do_extraction method not implemented by %s.', % self.class)

class PypiMetadataExtractor(MetadataExtractor):
    def __init__(self, pkg_data_obj, client, name, version):
        self.client = client
        self.name = name
        self.version = version

    def extract_data(self):
        release_urls = self.client.release_urls(name, version)

class LocalMetadataExtractor(MetadataExtractor):
    pass
