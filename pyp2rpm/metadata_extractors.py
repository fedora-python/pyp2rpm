import os
import re

from pyp2rpm import archive
from pyp2rpm.dependency_parser import DependencyParser
from pyp2rpm.package_data import PypiData, LocalData
from pyp2rpm import settings
from pyp2rpm import utils


class MetadataExtractor(object):
    """Base class for metadata extractors"""
    def __init__(self, local_file, name, name_convertor, version):
        self.local_file = local_file
        self.archive = archive.Archive(local_file)
        self.name = name
        self.name_convertor = name_convertor
        self.version = version

    def extract_data(self):
        raise NotImplementedError('Whoops, extract_data method not implemented by {0}.'.format(self.__class__))

    def name_convert_deps_list(self, deps_list):
        for dep in deps_list:
            dep[1] = self.name_convertor.rpm_name(dep[1])

        return deps_list

    @property
    def runtime_deps_from_setup_py(self): # install_requires
        """ Returns list of runtime dependencies of the package specified in setup.py.

        Dependencies are in RPM SPECFILE format - see DependencyParser.dependency_to_rpm() for details, but names are already
        transformed according to current distro.

        Returns:
            list of runtime dependencies of the package
        """
        return self.name_convert_deps_list(DependencyParser.deps_from_pyp_format(self.archive.find_list_argument('install_requires'), runtime = True))

    @property
    def build_deps_from_setup_py(self): # setup_requires
        """Same as runtime_deps_from_setup_py, but build dependencies.

        Returns:
            list of build dependencies of the package
        """
        return self.name_convert_deps_list(DependencyParser.deps_from_pyp_format(self.archive.find_list_argument('setup_requires'), runtime = False))

    @property
    def runtime_deps_from_egg_info(self):
        """ Returns list of runtime dependencies of the package specified in EGG-INFO/requires.txt.

        Dependencies are in RPM SPECFILE format - see DependencyParser.dependency_to_rpm() for details, but names are already
        transformed according to current distro.

        Returns:
            list of runtime dependencies of the package
        """
        requires_txt = self.archive.get_content_of_file('EGG-INFO/requires.txt', True) or ''
        return self.name_convert_deps_list(DependencyParser.deps_from_pyp_format(requires_txt.splitlines()))

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
    def doc_files(self):
        """Returns list of doc files that should be used for %doc in specfile.
        Returns:
            List of doc files from the archive - only basenames, not full paths.
        """
        doc_files = []
        for doc_file_re in settings.DOC_FILES_RE:
            doc_files.extend(self.archive.get_files_re(doc_file_re, ignorecase = True))

        return list(map(lambda x: os.path.basename(x), doc_files))

    @property
    def sphinx_dir(self):
        """Returns directory with sphinx documentation, if there is such.
        Returns:
            Full path to sphinx documentation dir inside the archive, or None if there is no such.
        """
        sphinx_dir = None

        # search for sphinx dir doc/ or docs/ under the first directory in archive (e.g. spam-1.0.0/doc)
        candidate_dirs = self.archive.get_directories_re(settings.SPHINX_DIR_RE, full_path = True)
        for d in candidate_dirs: # search for conf.py in the dirs (TODO: what if more are found?)
            contains_conf_py = len(self.archive.get_files_re(r'{0}/conf.py'.format(d), full_path = True)) > 0
            if contains_conf_py == True:
                sphinx_dir = d

        return sphinx_dir

    @property
    def has_packages(self):
        return self.archive.has_argument('packages')

    @property
    def has_py_modules(self):
        return self.archive.has_argument('py_modules')

    @property
    def py_modules(self):
        return self.archive.find_list_argument('py_modules')

    @property
    def scripts(self):
        scripts = self.archive.find_list_argument('scripts')
        # handle the case for 'console_scripts' = [ 'a = b' ]
        transformed = []
        for script in scripts:
            equal_sign = script.find('=')
            if equal_sign == -1:
                transformed.append(script)
            else:
                transformed.append(script[0:equal_sign].strip())

        return map(os.path.basename, transformed)

    @property
    def data_from_archive(self):
        """Returns all metadata extractable from the archive.
        Returns:
            dictionary containing metadata extracted from the archive
        """
        archive_data = {}
        archive_data['has_extension'] = self.has_extension
        archive_data['has_bundled_egg_info'] = self.has_bundled_egg_info
        archive_data['doc_files'] = self.doc_files
        if self.archive.is_egg:
            archive_data['runtime_deps'] = self.runtime_deps_from_egg_info
            archive_data['build_deps'] = self.build_deps_from_egg_info
        else:
            archive_data['runtime_deps'] = self.runtime_deps_from_setup_py
            archive_data['build_deps'] = self.build_deps_from_setup_py

        sphinx_dir = self.sphinx_dir
        if sphinx_dir:
            archive_data['sphinx_dir'] = os.path.basename(sphinx_dir)
            archive_data['build_deps'].append(['BuildRequires', 'python-sphinx'])

        archive_data['has_packages'] = self.has_packages
        archive_data['py_modules'] = self.py_modules
        archive_data['scripts'] = self.scripts

        return archive_data

class PypiMetadataExtractor(MetadataExtractor):
    def __init__(self, local_file, name, name_convertor, version, client):
        super(PypiMetadataExtractor, self).__init__(local_file, name, name_convertor, version)
        self.client = client

    def extract_data(self):
        """Extracts data from PyPI and archive.
        Returns:
            PypiData object containing data extracted from PyPI and archive.
        """
        try:
            release_urls = self.client.release_urls(self.name, self.version)
            release_data = self.client.release_data(self.name, self.version)
        except: # some kind of error with client => return TODO: log the failure
            return PypiData(self.local_file,
                            self.name,
                            self.name_convertor.rpm_name(self.name),
                            self.version,
                            'FAILED TO EXTRACT FROM PYPI',
                            'FAILED TO EXTRACT FROM PYPI')

        url = ''
        md5_digest = None

        if len(release_urls) > 0:
            url = release_urls[0]['url']
            md5_digest = release_urls[0]['md5_digest']
        elif release_data:
            url = release_data['download_url']

        data = PypiData(self.local_file,
                        self.name,
                        self.name_convertor.rpm_name(self.name),
                        self.version,
                        md5_digest,
                        url)
        for data_field in settings.PYPI_USABLE_DATA:
            setattr(data, data_field, release_data.get(data_field, ''))

        # we usually get better license representation from trove classifiers
        data.license = utils.license_from_trove(release_data.get('classifiers', '')) or data.license

        with self.archive:
            data.set_from(self.data_from_archive)

        return data

class LocalMetadataExtractor(MetadataExtractor):
    def __init__(self, local_file, name, name_convertor, version):
        super(LocalMetadataExtractor, self).__init__(local_file, name, name_convertor, version)

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
        data = LocalData(self.local_file,
                         self.name,
                         self.name_convertor.rpm_name(self.name),
                         self.version)

        with self.archive:
            data.set_from(self.data_from_archive)
            data.license = self.license_from_archive

        return data
