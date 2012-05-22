import os
import re

from pyp2rpmlib import archive
from pyp2rpmlib.dependency_parser import DependencyParser
from pyp2rpmlib.package_data import PypiData, LocalData
from pyp2rpmlib import settings
from pyp2rpmlib import utils


class MetadataExtractor(object):
    """Base class for metadata extractors"""
    def __init__(self, local_file, name, version):
        self.local_file = local_file
        self.archive = archive.Archive(local_file)
        self.name = name
        self.version = version

    def extract_data(self):
        raise NotImplementedError('Whoops, extract_data method not implemented by %s.' % self.__class__)

    @property
    def runtime_deps_from_setup_py(self): # install_requires
        """ Returns list of runtime dependencies of the package specified in setup.py.

        Dependencies are in RPM SPECFILE format - see DependencyParser.dependency_to_rpm() for details.

        Returns:
            list of runtime dependencies of the package
        """
        return DependencyParser.deps_from_pyp_format(self.archive.find_list_argument('install_requires'), runtime = True)

    @property
    def build_deps_from_setup_py(self): # setup_requires
        """Same as runtime_deps_from_setup_py, but build dependencies.

        Returns:
            list of build dependencies of the package
        """
        return DependencyParser.deps_from_pyp_format(self.archive.find_list_argument('setup_requires'), runtime = False)

    @property
    def runtime_deps_from_egg_info(self):
        """ Returns list of runtime dependencies of the package specified in EGG-INFO/requires.txt.

        Dependencies are in RPM SPECFILE format - see DependencyParser.dependency_to_rpm() for details.

        Returns:
            list of runtime dependencies of the package
        """
        requires_txt = self.archive.get_content_of_file('EGG-INFO/requires.txt', True) or ''
        return DependencyParser.deps_from_pyp_format(requires_txt.splitlines())

    @property
    def build_deps_from_egg_info(self):
        """Stub"""
        return []

    @property
    def has_bundled_egg_info(self):
        """Finds out if there is a bundled .egg-info dir in the archive.
        Returns:
            True if the archive contains bundled .egg-info directory, False otherwise
        """
        return self.archive.has_file_with_suffix('.egg-info')

    @property
    def has_extension(self):
        """Finds out whether the packages has binary extension.
        Returns:
            True if the package has a binary extension, False otherwise
        """
        return self.archive.has_file_with_suffix(settings.EXTENSION_SUFFIXES)

    @property
    def data_from_archive(self):
        """Returns all metadata extractable from the archive.
        Returns:
            dictionary containing metadata extracted from the archive
        """
        archive_data = {}
        archive_data['has_extension'] = self.has_extension
        archive_data['has_bundled_egg_info'] = self.has_bundled_egg_info
        if self.archive.is_egg:
            archive_data['runtime_deps'] = self.runtime_deps_from_egg_info
            archive_data['build_deps'] = self.build_deps_from_egg_info
        else:
            archive_data['runtime_deps'] = self.runtime_deps_from_setup_py
            archive_data['build_deps'] = self.build_deps_from_setup_py

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

        with self.archive:
            data.set_from(self.data_from_archive)

        return data

class LocalMetadataExtractor(MetadataExtractor):
    def __init__(self, local_file, name, version):
        super(LocalMetadataExtractor, self).__init__(local_file, name, version)

    @property
    def license_from_archive(self):
        if self.local_file.endswith('.egg'):
            return self.license_from_egg_info
        else:
            return self.license_from_setup_py

    @property
    def license_from_setup_py(self):
        return utils.license_from_trove(self.archive.find_list_argument('classifiers'))

    @property
    def license_from_egg_info(self):
        return utils.license_from_trove(self.archive.get_content_of_file('EGG-INFO/PKG-INFO', True).splitlines())

    def extract_data(self):
        """Extracts data from archive.
        Returns:
            LocalData object containing the extracted data.
        """
        data = LocalData(self.local_file, self.name, self.version)

        with self.archive:
            data.set_from(self.data_from_archive)
            data.license = self.license_from_archive

        return data
