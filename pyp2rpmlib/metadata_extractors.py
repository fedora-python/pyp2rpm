import os
import re

from pyp2rpmlib.package_data import PypiData, LocalData
from pyp2rpmlib.requirements_parser import RequirementsParser
from pyp2rpmlib import settings
from pyp2rpmlib import utils


class MetadataExtractor(object):
    def __init__(self, local_file, name, version):
        self.local_file = local_file
        self.name = name
        self.version = version

    def extract_data(self):
        raise NotImplementedError('Whoops, extract_data method not implemented by %s.' % self.__class__)

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

    @utils.memoize_by_args
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

    def find_array_argument(self, setup_argument): # very stupid method to find an array argument of setup()
        setup_py = self.get_content_of_file_from_archive('setup.py')
        if not setup_py: return []

        argument = []
        start_braces = end_braces = 0
        cont = False

        for line in setup_py.splitlines():
            if line.find(setup_argument) != -1 or cont:
                start_braces += line.count('[')
                end_braces += line.count(']')

                cont = True
                argument.append(line)
                if start_braces == end_braces:
                    break

        if not argument:
            return []
        else:
            argument[0] = argument[0][argument[0].find('['):]
            argument[-1] = argument[-1].rstrip().rstrip(',')
            return eval(' '.join(argument).strip())

    @property
    def runtime_deps_from_setup_py(self): # install_requires
        return RequirementsParser.deps_from_setup_py(self.find_array_argument('install_requires'), runtime = True)

    @property
    def build_deps_from_setup_py(self): # setup_requires
        return RequirementsParser.deps_from_setup_py(self.find_array_argument('setup_requires'), runtime = False)

    def has_file_with_suffix(self, suffixes):
        name, suffix = os.path.splitext(self.local_file)
        extractor = self.get_extractor_cls(suffix)
        has_file = False

        if extractor:
            with extractor.open(name = self.local_file) as opened_file:
                for member in opened_file.getmembers():
                    if os.path.splitext(member.name)[1] in suffixes:
                        has_file = True

    @property
    def has_bundled_egg_info(self):
        return self.has_file_with_suffix('.egg-info')

    @property
    def has_extension(self):
        return self.has_file_with_suffix(settings.EXTENSION_SUFFIXES)

    @property
    def data_from_archive(self):
        archive_data = {}
        archive_data['has_extension'] = self.has_extension
        archive_data['has_bundled_egg_info'] = self.has_bundled_egg_info
        archive_data['runtime_deps_from_setup_py'] = self.runtime_deps_from_setup_py
        archive_data['build_deps_from_setup_py'] = self.build_deps_from_setup_py

        return archive_data

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

        for k, v in self.data_from_archive.iteritems():
            setattr(data, k, v)

        return data

class LocalMetadataExtractor(MetadataExtractor):
    def __init__(self, local_file, name, version):
        super(LocalMetadataExtractor, self).__init__(local_file, name, version)
