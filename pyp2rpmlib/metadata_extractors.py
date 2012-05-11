import xmlrpclib

from pyp2rpmlib.package_data import PypiData, LocalData
from pyp2rpmlib import settings

class MetadataExtractor(object):
    def __init__(self, name, version):
        self.name = name
        self.version = version

    def extract_data(self):
        raise NotImplementedError('Whoops, do_extraction method not implemented by %s.', % self.class)

class PypiMetadataExtractor(MetadataExtractor):
    def __init__(self, client, name, version):
        super(MetadataExtractor, self).__init__(name, version)
        self.client = client

    def extract_data(self):
        release_urls = self.client.release_urls(self.name, self.version)[0]
        release_data = self.client.release_data(self.name, self.version)
        data = PypiData(self.name, self.version, release_urls['md5_digest'], release_urls['url'])
        for data_field in settings.PYPI_USABLE_DATA:
            setattr(data, data_field, release_data[data_field])

        # if license is not known, try to extract if from trove classifiers
        if data.license in [None, 'UNKNOWN']:
            data.license = []
            for classifier in release_data['classifiers']:
                if classifier.find('License') != -1:
                    data.license.append(settings.TROVE_LICENSES.get(classifier, 'UNKNOWN'))

            data.license = ' AND '.join(data.license)

        return data

class LocalMetadataExtractor(MetadataExtractor):
    def __init__(self, local_file, name, version):
        super(MetadataExtractor, self).__init__(name, version)
        self.local_file = local_file
