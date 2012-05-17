import os
import re

from tarfile import TarFile
from zipfile import ZipFile, ZipInfo

from pyp2rpmlib.package_data import PypiData, LocalData
from pyp2rpmlib.requirements_parser import DependencyParser
from pyp2rpmlib import settings
from pyp2rpmlib import utils

ZipFile.getmembers = ZipFile.infolist
ZipFile.extractfile = ZipFile.open
ZipFile.open = ZipFile
ZipInfo.name = ZipInfo.filename

class MetadataExtractor(object):
    """Base class for metadata extractors"""
    def __init__(self, local_file, name, version):
        self.local_file = local_file
        self.name = name
        self.version = version

    def extract_data(self):
        raise NotImplementedError('Whoops, extract_data method not implemented by %s.' % self.__class__)

    def get_extractor_cls(self, suffix):
        """Returns the class that can read the archive based on archive suffix.
        Args:
            suffix: the suffix (extension) of the archive file (with leading ".", e.g. not "tar", but ".tar")
        Returns:
            class that can read the archive or None if no such exists
        """
        file_cls = None

        # only catches ".gz", even from ".tar.gz"
        if suffix in ['.tar', '.gz', '.bz2']:
            file_cls = TarFile
        elif suffix in ['.zip']:
            file_cls = ZipFile
        else:
            pass
            # TODO: log that file has unextractable archive suffix and we can't look inside the archive

        return file_cls

    @utils.memoize_by_args
    def get_content_of_file_from_archive(self, name): # TODO: extend to be able to match whole path in archive
        """Returns content of file from archive.

        So far this only considers name, not full path in the archive. Therefore if two such files exist,
        content of one is returned (it is not specified which one that is).

        Args:
            name: name of the file to get content of
        Returns:
            Content of the file with given name or None, if no such.
        """
        suffix = os.path.splitext(self.local_file)[1]
        extractor = self.get_extractor_cls(suffix)

        if extractor:
            with extractor.open(self.local_file) as opened_file:
                for member in opened_file.getmembers():
                    if os.path.basename(member.name) == name:
                        extracted = opened_file.extractfile(member)
                        return extracted.read()

        return None

    def find_list_argument(self, setup_argument):
        """A simple method that gets setup() function from setup.py list argument like install_requires.

        Will not work in all cases and might need a smarter approach.

        Args:
            setup_argument: name of the argument of setup() function to get value of
        Returns:
            The requested setup() argument or empty list, if setup.py can't be open.
        """
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
        """ Returns list of runtime dependencies of the package specified in setup.py.

        Dependencies are in RPM SPECFILE format - see DependencyParser.dependency_to_rpm() for details.

        Returns:
            list of runtime dependencies of the package
        """
        return DependencyParser.deps_from_setup_py(self.find_list_argument('install_requires'), runtime = True)

    @property
    def build_deps_from_setup_py(self): # setup_requires
        """Same as runtime_deps_from_setup_py, but build dependencies.

        Returns:
            list of build dependencies of the package
        """
        return DependencyParser.deps_from_setup_py(self.find_list_argument('setup_requires'), runtime = False)

    def has_file_with_suffix(self, suffixes):
        """Finds out if there is a file with one of suffixes in the archive.
        Args:
            suffixes: list of suffixes to look for
        Returns:
            True if there is at least one file with at least one given suffix in the archive, False otherwise
        """

        name, suffix = os.path.splitext(self.local_file)
        extractor = self.get_extractor_cls(suffix)
        has_file = False

        if extractor:
            with extractor.open(self.local_file) as opened_file:
                for member in opened_file.getmembers():
                    if os.path.splitext(member.name)[1] in suffixes:
                        has_file = True

    @property
    def has_bundled_egg_info(self):
        """Finds out if there is a bundled .egg-info dir in the archive.
        Returns:
            True if the archive contains bundled .egg-info directory, False otherwise
        """
        return self.has_file_with_suffix('.egg-info')

    @property
    def has_extension(self):
        """Finds out whether the packages has binary extension.
        Returns:
            True if the package has a binary extension, False otherwise
        """
        return self.has_file_with_suffix(settings.EXTENSION_SUFFIXES)

    @property
    def data_from_archive(self):
        """Returns all metadata extractable from the archive.
        Returns:
            dictionary containing metadata extracted from the archive
        """
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
        """Extracts data from PyPI and archive.
        Returns:
            PypiData object containing data extracted from PyPI and archive.
        """
        release_urls = self.client.release_urls(self.name, self.version)[0]
        release_data = self.client.release_data(self.name, self.version)
        data = PypiData(self.local_file, self.name, self.version, release_urls['md5_digest'], release_urls['url'])
        for data_field in settings.PYPI_USABLE_DATA:
            setattr(data, data_field, release_data.get(data_field, None))

        # we usually get better license representation from trove classifiers
        data.license = utils.license_from_trove(release_data['classifiers']) or data.license

        for k, v in self.data_from_archive.iteritems():
            setattr(data, k, v)

        return data

class LocalMetadataExtractor(MetadataExtractor):
    def __init__(self, local_file, name, version):
        super(LocalMetadataExtractor, self).__init__(local_file, name, version)
