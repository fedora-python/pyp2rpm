import logging
import os
import sys
import re
import tempfile
import shutil
import itertools
import glob
from abc import ABCMeta, abstractmethod
try:
    import xmlrpclib
except ImportError:
    import xmlrpc.client as xmlrpclib

from pyp2rpm import archive
from pyp2rpm.dependency_parser import deps_from_pyp_format, deps_from_pydit_json
from pyp2rpm.exceptions import VirtualenvFailException
from pyp2rpm.package_data import PackageData
from pyp2rpm.package_getters import get_url
from pyp2rpm.logger import LoggerWriter
from pyp2rpm import settings
from pyp2rpm import utils
from pyp2rpm import extract_distribution
try:
    from pyp2rpm import virtualenv
except ImportError:
    virtualenv = None

logger = logging.getLogger(__name__)


def pypi_metadata_extension(extraction_fce):
    """Extracts data from PyPI and appends them to data returned from
    given data extraction method.
    """

    def inner(self, client=None):
        data = extraction_fce(self)
        try:
            if client is None:
                raise ValueError("Client is None.")
            release_data = client.release_data(self.name, self.version)
        except:
            logger.warning('Some kind of error while communicating with client: {0}.'.format(
                client), exc_info=True)
            return data

        url, md5_digest = get_url(client, self.name, self.version)
        data_dict = {'url': url, 'md5': md5_digest}

        for data_field in settings.PYPI_USABLE_DATA:
            data_dict[data_field] = release_data.get(data_field, '')

        # we usually get better license representation from trove classifiers
        data_dict["license"] = utils.license_from_trove(release_data.get('classifiers', ''))
        data.set_from(data_dict, update=True)
        return data
    return inner


class LocalMetadataExtractor(object):

    """Abstract base class for metadata extractors, does not provide
    implementation of main method to extract data.
    """

    __metaclass__ = ABCMeta

    def __init__(self, local_file, name, name_convertor, version,
                 rpm_name=None, venv=True,
                 base_python_version=settings.DEFAULT_PYTHON_VERSION,
                 metadata_extension=False):
        self.local_file = local_file
        self.archive = archive.Archive(local_file)
        self.name = name
        self.name_convertor = name_convertor
        self.version = version
        self.rpm_name = rpm_name
        self.venv = venv
        self.base_python_version = base_python_version
        self.metadata_extension = metadata_extension

    def name_convert_deps_list(self, deps_list):
        for dep in deps_list:
            dep[1] = self.name_convertor.rpm_name(dep[1])

        return deps_list

    @property
    def has_pth(self):
        """Figure out if package has pth file """
        return "." in self.name

    @property
    def has_extension(self):
        """Finds out whether the packages has binary extension.
        Returns:
            True if the package has a binary extension, False otherwise
        """
        return self.archive.has_file_with_suffix(settings.EXTENSION_SUFFIXES)

    @property
    def data_from_venv(self):
        """Returns all metadata extractable from virtualenv object.
        Returns:
            dictionary containing metadata extracted from virtualenv
        """
        if not self.venv:
            return {}

        temp_dir = tempfile.mkdtemp()
        try:
            extractor = virtualenv.VirtualEnv(self.name, temp_dir,
                                              self.name_convertor,
                                              self.base_python_version)
            return extractor.get_venv_data
        except VirtualenvFailException as e:
            logger.error("{}, skipping virtualenv metadata extraction".format(e))
            return {}
        finally:
            shutil.rmtree(temp_dir)

    @pypi_metadata_extension
    def extract_data(self):
        """Extracts data from archive.
        Returns:
            PackageData object containing the extracted data.
        """
        data = PackageData(self.local_file,
                           self.name,
                           self.name_convertor.rpm_name(self.name)
                           if self.rpm_name is None else self.rpm_name,
                           self.version)

        with self.archive:
            data.set_from(self.data_from_archive)

        if virtualenv is not None:
            data.set_from(self.data_from_venv, update=True)

        if "scripts" in data.data:
            setattr(data, "scripts", utils.remove_major_minor_suffix(data.data['scripts']))
        # for example nose has attribute `packages` but instead of name listing the pacakges
        # is using function to find them, that makes data.packages an empty set
        if data.has_packages and data.packages in ("TODO:", set()):
            data.packages = set([data.name])

        return data

    @property
    @abstractmethod
    def data_from_archive(self):
        pass


class SetupPyMetadataExtractor(LocalMetadataExtractor):
    """Class to extract metadata from setup.py"""

    @property
    def runtime_deps_from_setup_py(self):  # install_requires
        """ Returns list of runtime dependencies of the package specified in setup.py.

        Dependencies are in RPM SPECFILE format - see dependency_to_rpm() for details,
        but names are already
        transformed according to current distro.

        Returns:
            list of runtime dependencies of the package
        """
        install_requires = self.archive.find_list_argument('install_requires')
        if self.archive.has_argument('entry_points') and 'setuptools' not in install_requires:
            install_requires.append('setuptools')  # entrypoints

        return self.name_convert_deps_list(deps_from_pyp_format(install_requires, runtime=True))

    @property
    def build_deps_from_setup_py(self):  # setup_requires
        """Same as runtime_deps_from_setup_py, but build dependencies.

        Returns:
            list of build dependencies of the package
        """
        build_requires = self.archive.find_list_argument('setup_requires')
        if 'setuptools' in build_requires:
            build_requires.remove('setuptools')

        build = self.name_convert_deps_list(
            deps_from_pyp_format(build_requires, runtime=False))
        test = self.name_convert_deps_list(
            deps_from_pyp_format(self.archive.find_list_argument('tests_require'), runtime=False))

        return list(build + test)

    @property
    def runtime_deps_from_egg_info(self):
        """ Returns list of runtime dependencies of the package specified in EGG-INFO/requires.txt.

        Dependencies are in RPM SPECFILE format - see dependency_to_rpm() for details,
        but names are already transformed according to current distro.

        Returns:
            list of runtime dependencies of the package
        """
        requires_txt = self.archive.get_content_of_file(
            'EGG-INFO/requires.txt', True) or ''
        return self.name_convert_deps_list(deps_from_pyp_format(requires_txt.splitlines()))

    @property
    def has_bundled_egg_info(self):
        """Finds out if there is a bundled .egg-info dir in the archive.
        Returns:
            True if the archive contains bundled .egg-info directory, False otherwise
        """
        return self.archive.has_file_with_suffix('.egg-info')

    @property
    def has_test_suite(self):
        """Finds out whether the package contains setup.py test suite.
        Returns:
            True if the package contains setup.py test suite, False otherwise
        """
        return self.archive.has_argument('test_suite')

    @property
    def doc_files(self):
        """Returns list of doc files that should be used for %doc in specfile.
        Returns:
            List of doc files from the archive - only basenames, not full paths.
        """
        doc_files = []
        for doc_file_re in settings.DOC_FILES_RE:
            doc_files.extend(
                self.archive.get_files_re(doc_file_re, ignorecase=True))
        return ['/'.join(x.split('/')[1:]) for x in doc_files]

    @property
    def sphinx_dir(self):
        """Returns directory with sphinx documentation, if there is such.
        Returns:
            Full path to sphinx documentation dir inside the archive, or None if there is no such.
        """
        sphinx_dir = None

        # search for sphinx dir doc/ or docs/ under the first directory in
        # archive (e.g. spam-1.0.0/doc)
        candidate_dirs = self.archive.get_directories_re(
            settings.SPHINX_DIR_RE, full_path=True)
        for d in candidate_dirs:  # search for conf.py in the dirs (TODO: what if more are found?)
            contains_conf_py = len(self.archive.get_files_re(
                r'{0}/conf.py'.format(re.escape(d)), full_path=True)) > 0
            if contains_conf_py:
                sphinx_dir = d

        return sphinx_dir

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
        return utils.license_from_trove(self.archive.get_content_of_file(
            'EGG-INFO/PKG-INFO', True).splitlines())

    @property
    def versions_from_archive(self):
        if self.local_file.endswith('.egg'):
            trove = self.archive.get_content_of_file('EGG-INFO/PKG-INFO', True).splitlines()
        else:
            trove = self.archive.find_list_argument('classifiers')
        return utils.versions_from_trove(trove)

    @property
    def has_packages(self):
        return self.archive.has_argument('packages')

    @property
    def packages(self):
        # added because of Issue #8
        # https://bitbucket.org/bkabrda/pyp2rpm/issue/8/packaging-beets
        if self.has_packages:
            # usually packages list looks like `foo.bar.baz` but we are interested
            # only in `foo`
            packages = [package.split('.', 1)[0]
                        for package in self.archive.find_list_argument('packages')]
            return set(packages)

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

        return list(map(os.path.basename, transformed))

    @property
    def data_from_archive(self):
        """Returns all metadata extractable from the archive.
        Returns:
            dictionary containing metadata extracted from the archive
        """
        archive_data = {}

        archive_data['license'] = self.license_from_archive
        archive_data['has_pth'] = self.has_pth
        archive_data['scripts'] = self.scripts
        archive_data['has_extension'] = self.has_extension

        if self.archive.is_egg:
            archive_data['runtime_deps'] = self.runtime_deps_from_egg_info
            archive_data['build_deps'] = [['BuildRequires', 'python2-devel'],
                                          ['BuildRequires', 'python-setuptools']]
        else:
            archive_data['runtime_deps'] = self.runtime_deps_from_setup_py
            archive_data['build_deps'] = utils.unique_deps([['BuildRequires', 'python2-devel'],
                                                            ['BuildRequires', 'python-setuptools']]
                                                           + self.build_deps_from_setup_py)

        py_vers = self.versions_from_archive
        archive_data['base_python_version'] = py_vers[0] if py_vers \
            else settings.DEFAULT_PYTHON_VERSION
        archive_data['python_versions'] = py_vers[1:] if py_vers \
            else [settings.DEFAULT_ADDITIONAL_VERSION]

        archive_data['doc_files'] = self.doc_files
        archive_data['py_modules'] = self.py_modules
        archive_data['has_test_suite'] = self.has_test_suite
        archive_data['has_bundled_egg_info'] = self.has_bundled_egg_info
        archive_data['has_packages'] = self.has_packages
        archive_data['packages'] = self.packages

        sphinx_dir = self.sphinx_dir
        if sphinx_dir:
            archive_data['sphinx_dir'] = "/".join(sphinx_dir.split("/")[1:])
            archive_data['build_deps'].append(
                ['BuildRequires', 'python-sphinx'])

        return archive_data


class DistMetadataExtractor(SetupPyMetadataExtractor):
    """Metadata extractor based on bdist_rpm distutils command"""

    def __init__(self, *args, **kwargs):
        super(DistMetadataExtractor, self).__init__(*args, **kwargs)

        temp_dir = tempfile.mkdtemp()
        try:
            with self.archive as a:
                a.extract_all(directory=temp_dir)
                try:
                    setup_py = glob.glob(temp_dir + "/{0}*/".format(self.name) + 'setup.py')[0]
                except IndexError:
                    sys.stderr.write(
                        "setup.py not found, maybe local_file is not proper source archive.\n")
                    raise SystemExit(3)

                with utils.ChangeDir(os.path.dirname(setup_py)):
                    with utils.RedirectStdStreams(stdout=LoggerWriter(logger.debug),
                                                  stderr=LoggerWriter(logger.warning)):
                        extract_distribution.run_setup(setup_py, 'bdist_rpm')

                self.distribution = extract_distribution.extract_distribution.class_distribution
        finally:
            shutil.rmtree(temp_dir)

    @property
    def license_from_archive(self):
        return self.distribution.get_license()

    @property
    def runtime_deps_from_setup_py(self):
        return self.name_convert_deps_list(deps_from_pyp_format(self.distribution.run_requires))

    @property
    def build_deps_from_setup_py(self):
        return self.name_convert_deps_list(deps_from_pyp_format(self.distribution.build_requires,
                                                                runtime=False))

    @property
    def conflicts(self):
        return self.name_convert_deps_list(self.distribution.conflicts)

    @property
    def versions_from_archive(self):
        return utils.versions_from_trove(self.distribution.metadata.classifiers)

    @property
    def long_description(self):
        """Shorten description on first newline after approx 10 lines"""
        if not self.distribution.metadata.long_description:
            return ''
        cut = self.distribution.metadata.long_description.find('\n', 80 * 8)
        if cut > -1:
            return self.distribution.metadata.long_description[:cut] + '\n...'
        else:
            return self.distribution.metadata.long_description

    @property
    def data_from_archive(self):
        """Returns all metadata extractable from distutils distribution object
        Returns:
            dictionary containing extracted metadata
        """
        archive_data = super(DistMetadataExtractor, self).data_from_archive

        if not self.distribution.force_arch:
            if not self.distribution.has_ext_modules():
                archive_data['build_arch'] = 'noarch'
        else:
            archive_data['build_arch'] = self.distribution.force_arch

        archive_data['description'] = self.long_description
        archive_data['summary'] = self.distribution.get_description()
        archive_data['home_page'] = self.distribution.get_url()
        archive_data['icon'] = getattr(self.distribution, 'icon', None)

        archive_data['prep_cmd'] = getattr(self.distribution, 'prep', settings.DEFAULT_PREP)
        archive_data['build_cmd'] = getattr(self.distribution, 'build', settings.DEFAULT_BUILD)
        archive_data['install_cmd'] = getattr(
            self.distribution, 'install', settings.DEFAULT_INSTALL)
        archive_data['clean_cmd'] = getattr(self.distribution, 'clean', settings.DEFAULT_CLEAN)

        return archive_data


class WheelMetadataExtractor(LocalMetadataExtractor):
    """Class to extract metadata from wheel archive"""

    @property
    def json_metadata(self):
        if not hasattr(self, '_json_metadata'):
            self._json_metadata = self.archive.json_wheel_metadata
        return self._json_metadata

    @property
    def doc_files(self):
        return set([doc for doc in self.json_metadata.get('extensions', {})
                                                     .get('python.details', {})
                                                     .get('document_names', {}).values()])

    @property
    def home_page(self):
        urls = [url for url in self.json_metadata.get('extensions', {})
                                                 .get('python.details', {})
                                                 .get('project_urls', {}).values()]
        if urls:
            return urls[0]

    def get_requires(self, requires_types):
        "Extracts requires of given types from metadata file, filter windows specific requires"
        # TODO extras?
        if not isinstance(requires_types, list):
            requires_types = list(requires_types)
        extracted_requires = []
        for requires_name in requires_types:
            for requires in self.json_metadata.get(requires_name, []):
                if 'win' in requires.get('environment', {}):
                    continue
                extracted_requires.extend(requires['requires'])
        return extracted_requires

    @property
    def license(self):
        return self.json_metadata.get('license', None)

    @property
    def summary(self):
        return self.json_metadata.get('summary', None)

    @property
    def runtime_deps(self):
        run_requires = self.get_requires(['run_requires', 'meta_requires'])
        return self.name_convert_deps_list(deps_from_pydit_json(run_requires))

    @property
    def build_deps(self):
        build_requires = self.get_requires(['build_requires', 'test_requires'])
        return self.name_convert_deps_list(deps_from_pydit_json(build_requires, runtime=False))

    @property
    def modules(self):
        return self.archive.record.get('modules')

    @property
    def scripts(self):
        return self.archive.record.get('scripts', [])

    @property
    def has_test_suite(self):
        return self.json_metadata.get('test_requires', False) is not False

    @property
    def classifiers(self):
        return self.json_metadata.get('classifiers', [])

    @property
    def versions_from_archive(self):
        return utils.versions_from_trove(self.classifiers)

    @property
    def description(self):
        return self.archive.wheel_description()

    @property
    def data_from_archive(self):
        """Returns all metadata extractable from the whl pydist.json
        Returns:
            dictionary containing metadata extracted from json data
        """
        archive_data = {}
        archive_data['license'] = self.license
        archive_data['summary'] = self.summary
        archive_data['home_page'] = self.home_page
        archive_data['doc_files'] = self.doc_files
        archive_data['has_pth'] = self.has_pth
        archive_data['runtime_deps'] = utils.unique_deps(self.runtime_deps)
        archive_data['build_deps'] = utils.unique_deps([['BuildRequires', 'python2-devel'],
                                                        ['BuildRequires', 'python-setuptools']]
                                                       + self.build_deps)
        archive_data['py_modules'] = self.modules
        archive_data['scripts'] = self.scripts
        archive_data['has_test_suite'] = self.has_test_suite
        archive_data['has_extension'] = self.has_extension

        py_vers = self.versions_from_archive
        archive_data['base_python_version'] = py_vers[0] if py_vers \
            else settings.DEFAULT_PYTHON_VERSION
        archive_data['python_versions'] = py_vers[1:] if py_vers \
            else [settings.DEFAULT_ADDITIONAL_VERSION]

        archive_data['description'] = self.description
        return archive_data
