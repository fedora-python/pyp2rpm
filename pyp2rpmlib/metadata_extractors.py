import functools
import os

from pyp2rpmlib.package_data import PypiData, LocalData
from pyp2rpmlib import settings

def memoize_by_args(func):
    memory = {}

    @functools.wraps(func)
    def memoized(*args):
        if not args in memory.keys():
            value = func(*args)
            memory[args] = value

        return memory[args]

    return memoized


class MetadataExtractor(object):
    def __init__(self, local_file, name, version):
        self.local_file = local_file
        self.name = name
        self.version = version

    def extract_data(self):
        raise NotImplementedError('Whoops, do_extraction method not implemented by %s.' % self.__class__)

    def get_extractor_cls(self, suffix):
        file_cls = None

        # only catches ".gz", even from ".tar.gz"
        if suffix in ['.tar', '.gz', '.bz2']:
            from tarfile import TarFile
            file_cls = TarFile
        elif suffix in ['.zip']:
            from zipfile import ZipFile
            file_cls = ZipFile
        else:
            pass
            # TODO: log that file has unextractable archive suffix and we can't look inside the archive

        return file_cls

    @memoize_by_args
    def get_content_of_file_from_archive(self, name): # TODO: extend to be able to match whole path in archive
        suffix = os.path.splitext(self.local_file)[1]
        extractor = self.get_extractor_cls(suffix)

        if extractor:
            with extractor.open(name = self.local_file) as opened_file:
                for member in opened_file.getmembers():
                    if os.path.basename(member.name) == name:
                        extracted = opened_file.extractfile(member)
                        return extracted.read()

        return None

    def find_setup_argument(self, setup_argument):
        pass

    def requires_from_setup_py(self): # install_requires
        pass

    def build_requires_from_setup_py(self): # setup_requires
        pass

    def has_file_with_suffix(self, suffixes):
        name, suffix = os.path.splitext(self.local_file)
        extractor = self.get_extractor_cls(suffix)
        has_file = False

        if extractor:
            with extractor.open(name = self.local_file) as opened_file:
                for member in opened_file.getmembers():
                    if os.path.splitext(member.name)[1] in suffixes:
                        has_file = True

    def has_bundled_egg_info(self):
        return self.has_file_with_suffix('.egg-info')

    def has_extension(self):
        return self.has_file_with_suffix(settings.EXTENSION_SUFFIXES)

class PypiMetadataExtractor(MetadataExtractor):
    def __init__(self, local_file, name, version, client):
        super(PypiMetadataExtractor, self).__init__(local_file, name, version)
        self.client = client

    def extract_data(self):
        release_urls = self.client.release_urls(self.name, self.version)[0]
        release_data = self.client.release_data(self.name, self.version)
        data = PypiData(self.local_file, self.name, self.version, release_urls['md5_digest'], release_urls['url'])
        for data_field in settings.PYPI_USABLE_DATA:
            setattr(data, data_field, release_data.get(data_field, None))

        # if license is not known, try to extract if from trove classifiers
        if data.license in [None, 'UNKNOWN']:
            data.license = []
            for classifier in release_data['classifiers']:
                if classifier.find('License') != -1:
                    data.license.append(settings.TROVE_LICENSES.get(classifier, 'UNKNOWN'))

            data.license = ' AND '.join(data.license)

        data.has_extension = self.has_extension()
        data.has_bundled_egg_info = self.has_bundled_egg_info()

        return data

class LocalMetadataExtractor(MetadataExtractor):
    def __init__(self, local_file, name, version):
        super(LocalMetadataExtractor, self).__init__(local_file, name, version)
