import os
import xmlrpclib

from pyp2rpmlib.package_data import PypiData, LocalData
from pyp2rpmlib import settings

class MetadataExtractor(object):
    def __init__(self, local_file, name, version):
        self.local_file = local_file
        self.name = name
        self.version = version

    def extract_data(self):
        raise NotImplementedError('Whoops, do_extraction method not implemented by %s.', % self.class)

    def get_extractor_cls(self, suffix):
        file_cls = None

        if suffix in ['.tar', '.gz', '.bz2']:
            from tarfile import TarFile
            file_cls = TarFile
        elif suffix in ['.zip']:
            from zipfile import ZipFile
            file_cls = ZipFile
        else:
            pass
            # TODO: log that file has unextractable archive suffix and we can't look for extensions

        return file_cls

    def has_extension(self):
        # only catches ".gz", even from ".tar.gz"
        name, suffix = os.path.splitext(self.local_file)
        extractor = self.get_extractor_cls(suffix)
        # return True by default
        has_extension = True
        found_extension = False

        if extractor:
            opened_file = extractor.open(name = self.local_file)
            for member in opened_file.getmembers():
                if os.path.splitext(member.name)[1] in settings.EXTENSION_SUFFIXES:
                    found_extension = True
            has_extension = found_extension

        return has_extension

class PypiMetadataExtractor(MetadataExtractor):
    def __init__(self, client, local_file, name, version):
        super(MetadataExtractor, self).__init__(local_file, name, version)
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
        super(MetadataExtractor, self).__init__(name, version, local_file)
