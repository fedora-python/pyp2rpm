import xmlrpclib

from pyp2rpmlib.package_data import PackageData

class MetadataExtractor(object):
    def __init__(self, pkg_data_obj):
        self.pkg_data_obj = pkg_data_obj

    def do_extraction(self):
        raise NotImplementedError('Whoops, do_extraction method not implemented by %s.', % self.class)

class PypiMetadataExtractor(MetadataExtractor):
    def __init__(self, pkg_data_obj, client, name, version):
        super(MetadataExtractor, self).__init__(pkg_data_obj)
        self.client = client
        self.name = name
        self.version = version

    def do_extraction(self):
        
