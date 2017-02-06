import logging
import os
import sys
import json
import re
import tempfile
import shutil
import glob
import textwrap
from abc import ABCMeta
try:
    JSONDecodeError = json.decoder.JSONDecodeError
except AttributeError:
    JSONDecodeError = ValueError

import pyp2rpm.exceptions as exc
from pyp2rpm import archive
from pyp2rpm.dependency_parser import deps_from_pyp_format, deps_from_pydit_json
from pyp2rpm.package_data import PackageData
from pyp2rpm.package_getters import get_url
from pyp2rpm.module_runners import SubprocessModuleRunner
from pyp2rpm import settings
from pyp2rpm import utils
try:
    from pyp2rpm import virtualenv
except ImportError:
    virtualenv = None

logger = logging.getLogger(__name__)


def pypi_metadata_extension(extraction_fce):
    """Extracts data from PyPI and merges them with data from extraction method."""

    def inner(self, client=None):
        data = extraction_fce(self)
        if client is None:
            logger.warning("Client is None, it was probably disabled")
            return data
        try:
            release_data = client.release_data(self.name, self.version)
        except:
            logger.warning('Some kind of error while communicating with client: {0}.'.format(
                client), exc_info=True)
            return data
        try:
            url, md5_digest = get_url(client, self.name, self.version)
        except exc.MissingUrlException:
            url, md5_digest = ('FAILED TO EXTRACT FROM PYPI', 'FAILED TO EXTRACT FROM PYPI')
        data_dict = {'url': url, 'md5': md5_digest}

        for data_field in settings.PYPI_USABLE_DATA:
            data_dict[data_field] = release_data.get(data_field, '')

        # we usually get better license representation from trove classifiers
        data_dict["license"] = utils.license_from_trove(release_data.get('classifiers', ''))
        data.set_from(data_dict, update=True)
        return data
    return inner


def venv_metadata_extension(extraction_fce):
    """Extracts specific metadata from virtualenv object, merges them with data
    from given extraction method.
    """

    def inner(self):
        data = extraction_fce(self)
        if virtualenv is None or not self.venv:
            logger.debug("Skipping virtualenv metadata extraction.")
            return data

        temp_dir = tempfile.mkdtemp()
        try:
            extractor = virtualenv.VirtualEnv(self.name, temp_dir,
                                              self.name_convertor,
                                              self.base_python_version)
            data.set_from(extractor.get_venv_data, update=True)
        except exc.VirtualenvFailException as e:
            logger.error("{}, skipping virtualenv metadata extraction.".format(e))
        finally:
            shutil.rmtree(temp_dir)
        return data
    return inner


def process_description(description_fce):
    """Removes special character delimiters, titles
    and wraps paragraphs.
    """
    def inner(description):
                            # multiple whitespaces
        clear_description = re.sub(r'\s+', ' ',
                            # general URLs
                            re.sub(r'\w+:\/{2}[\d\w-]+(\.[\d\w-]+)*(?:(?:\/[^\s/]*))*', '',
                            # delimiters
                            re.sub('(#|-|=|~|`)*', '',
                            # very short lines, typically titles
                            re.sub('((\r?\n)|^).{0,8}((\r?\n)|$)', '',
                            # PyPI's version and downloads tags
                            re.sub('((\r*.. image::|:target:) https?|(:align:|:alt:))[^\n]*\n', '',
                                description_fce(description))))))
        return ' '.join(textwrap.wrap(clear_description, 80))
    return inner


class LocalMetadataExtractor(object):

    """Abstract base class for metadata extractors, does not provide
    implementation of main method to extract data.
    """

    __metaclass__ = ABCMeta

    def __init__(self, local_file, name, name_convertor, version,
                 rpm_name=None, venv=True,
                 base_python_version=None,
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
            dep[1] = self.name_convertor.rpm_name(dep[1], settings.DEFAULT_PYTHON_VERSION)

        return deps_list

    @property
    def has_pth(self):
        """Figure out if package has pth file """
        if virtualenv is None:
            return "." in self.name
        else:
            return None

    @property
    def has_extension(self):
        """Finds out whether the packages has binary extension.
        Returns:
            True if the package has a binary extension, False otherwise
        """
        return self.archive.has_file_with_suffix(settings.EXTENSION_SUFFIXES)

    @property
    def srcname(self):
        """Return srcname for the macro if the pypi name should be changed.

        Those cases are:
        - name was provided with -r option
        - pypi name is like python-<name>
        """
        if self.rpm_name or self.name.startswith(('python-', 'Python-')):
            return self.name_convertor.base_name(self.rpm_name or self.name)

    @pypi_metadata_extension
    @venv_metadata_extension
    def extract_data(self):
        """Extracts data from archive.
        Returns:
            PackageData object containing the extracted data.
        """
        data = PackageData(
            local_file=self.local_file,
            name=self.name,
            pkg_name=self.rpm_name or self.name_convertor.rpm_name(self.name),
            version=self.version,
            srcname=self.srcname)

        with self.archive:
            data.set_from(self.data_from_archive)

        if "scripts" in data.data:
            setattr(data, "scripts", utils.remove_major_minor_suffix(data.data['scripts']))
        # for example nose has attribute `packages` but instead of name listing the pacakges
        # is using function to find them, that makes data.packages an empty set
        # if virtualenv is disabled
        if virtualenv is None and getattr(data, "packages") == set():
            data.packages = set([data.name])

        return data

    @staticmethod
    def separate_license_files(doc_files):
        other = [doc for doc in doc_files if all(s not in doc.lower() for s in
                                                 settings.LICENSE_FILES)]
        licenses = [doc for doc in doc_files if any(s in doc.lower() for s in
                                                    settings.LICENSE_FILES)]
        return other, licenses

    @property
    def data_from_archive(self):
        """Returns all metadata extractable from the archive.
        Returns:
            dictionary containing metadata extracted from the archive
        """
        archive_data = {}

        archive_data['runtime_deps'] = self.runtime_deps
        archive_data['build_deps'] = [['BuildRequires', 'python2-devel']] + self.build_deps

        archive_data['py_modules'] = self.py_modules
        archive_data['scripts'] = self.scripts

        archive_data['home_page'] = self.home_page
        archive_data['description'] = self.description
        archive_data['summary'] = self.summary

        archive_data['license'] = self.license
        archive_data['has_pth'] = self.has_pth
        archive_data['has_extension'] = self.has_extension
        archive_data['has_test_suite'] = self.has_test_suite

        (archive_data['base_python_version'],
         archive_data['python_versions']) = self.versions_from_archive

        (archive_data['doc_files'],
         archive_data['doc_license']) = self.separate_license_files(self.doc_files)

        archive_data['dirname'] = self.archive.top_directory

        return archive_data


class SetupPyMetadataExtractor(LocalMetadataExtractor):
    """Class to extract metadata from setup.py using custom extract_dist command."""

    def __init__(self, *args, **kwargs):
        super(SetupPyMetadataExtractor, self).__init__(*args, **kwargs)

        self.unsupported_version = None
        temp_dir = tempfile.mkdtemp()
        try:
            with self.archive as package_archive:
                package_archive.extract_all(directory=temp_dir)
                self.metadata = self._get_metadata(temp_dir)
        finally:
            shutil.rmtree(temp_dir)

    def _get_metadata(self, temp_dir):
        runner = SubprocessModuleRunner(
            self.get_setup_py(temp_dir),
            *settings.EXTRACT_DIST_COMMAND_ARGS + ['--stdout'])

        current_version = self.base_python_version or str(sys.version_info[0])
        paths_to_attempt = (utils.get_interpreter_path(version=ver) for ver in (
            current_version,  # the version provided with `-b` option or default
            '2' if current_version == '3' else '3'  # alternative Python version
        ))
        for path in paths_to_attempt:
            try:
                logger.info("Running extract_dist command with: {0}".format(path))
                runner.run(path)
                return runner.results
            except (JSONDecodeError, exc.ExtractionError):
                logger.error("Could not extract metadata with: {0}".format(path))
                self.unsupported_version = current_version
        else:
            sys.stdout.write("Failed to extract data from setup.py script.\n")
            raise SystemExit(3)

    def get_setup_py(self, directory):
        try:
            return glob.glob("{0}/{1}*/setup.py".format(
                directory, self.archive.top_directory or self.name))[0]
        except IndexError:
            sys.stderr.write(
                "setup.py not found, maybe local_file is not proper source archive.\n")
            raise SystemExit(3)

    @property
    def runtime_deps(self):  # install_requires
        """Returns list of runtime dependencies of the package specified in setup.py.

        Dependencies are in RPM SPECFILE format - see dependency_to_rpm() for details,
        but names are already
        transformed according to current distro.

        Returns:
            list of runtime dependencies of the package
        """
        install_requires = self.metadata['install_requires']
        if self.metadata['entry_points'] and 'setuptools' not in install_requires:
            install_requires.append('setuptools')  # entrypoints

        return self.name_convert_deps_list(deps_from_pyp_format(install_requires, runtime=True))

    @property
    def build_deps(self):  # setup_requires + tests_require
        """Same as runtime_deps, but build dependencies. Test requires
        are included only if package contains test suite.

        Returns:
            list of build dependencies of the package
        """
        build_requires = self.metadata['setup_requires'] + self.metadata['tests_require']
        if 'setuptools' not in build_requires:
            build_requires.append('setuptools')
        return self.name_convert_deps_list(deps_from_pyp_format(
            build_requires, runtime=False))

    @property
    def has_packages(self):
        return self.metadata['packages'] != set()

    @property
    def packages(self):
        if self.has_packages:
            packages = [package.split('.', 1)[0]
                        for package in self.metadata['packages']]
            return set(packages)

    @property
    def py_modules(self):
        try:
            return set(self.metadata['py_modules'])
        except TypeError:
            return set()

    @property
    def scripts(self):
        transformed = []
        if self.metadata['entry_points']:
            scripts = self.metadata['entry_points'].get('console_scripts', [])
            # handle the case for 'console_scripts' = [ 'a = b' ]
            for script in scripts:
                equal_sign = script.find('=')
                if equal_sign == -1:
                    transformed.append(script)
                else:
                    transformed.append(script[0:equal_sign].strip())
        return set([os.path.basename(t) for t in transformed + self.metadata['scripts']])

    @property
    def home_page(self):
        return self.metadata['url']

    @property
    @process_description
    def long_description(self):
        return self.metadata['long_description']

    @property
    def description(self):
        """Shorten description on first newline after approx 10 lines"""
        cut = self.long_description.find('\n', 80 * 8)
        if cut > -1:
            return self.long_description[:cut] + '\n...'
        else:
            return self.long_description

    @property
    def summary(self):
        return self.metadata['description']

    @property
    def classifiers(self):
        return self.metadata['classifiers']

    @property
    def license(self):
        return self.metadata['license']

    @property
    def versions_from_archive(self):
        """Return Python versions extracted from trove classifiers or default.
        Returns:
            (str, list) base_python_version, python_versions
        """
        py_vers = utils.versions_from_trove(self.metadata['classifiers'])
        if self.unsupported_version in py_vers:
            py_vers.remove(self.unsupported_version)

        if not py_vers:
            py_vers = [settings.DEFAULT_PYTHON_VERSION,
                       settings.DEFAULT_ADDITIONAL_VERSION]
            if self.unsupported_version in py_vers:
                py_vers.remove(self.unsupported_version)

        return (py_vers[0], py_vers[1:])

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
        return self.metadata['test_suite'] or self.metadata['tests_require'] != []

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
        # search for sphinx dir doc/ or docs/ under the first directory in
        # archive (e.g. spam-1.0.0/doc)
        candidate_dirs = self.archive.get_directories_re(
            settings.SPHINX_DIR_RE, full_path=True)

        for directory in candidate_dirs:  # search for conf.py in the dirs (TODO: what if more are found?)
            contains_conf_py = self.archive.get_files_re(
                r'{0}/conf.py$'.format(re.escape(directory)), full_path=True)
            in_tests = 'tests' in directory.split(os.sep)
            if contains_conf_py and not in_tests:
                return directory

    @property
    def data_from_archive(self):
        """Appends setup.py specific metadata to archive_data."""

        archive_data = super(SetupPyMetadataExtractor, self).data_from_archive

        archive_data['has_packages'] = self.has_packages
        archive_data['packages'] = self.packages
        archive_data['has_bundled_egg_info'] = self.has_bundled_egg_info
        sphinx_dir = self.sphinx_dir
        if sphinx_dir:
            archive_data['sphinx_dir'] = "/".join(sphinx_dir.split("/")[1:])
            archive_data['build_deps'].append(
                ['BuildRequires', 'python-sphinx'])

        return archive_data


class WheelMetadataExtractor(LocalMetadataExtractor):
    """Class to extract metadata from wheel archive"""

    @property
    def json_metadata(self):
        if not hasattr(self, '_json_metadata'):
            self._json_metadata = self.archive.json_wheel_metadata
        return self._json_metadata

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
    def runtime_deps(self):
        run_requires = self.get_requires(['run_requires', 'meta_requires'])
        if 'setuptools' not in run_requires:
            run_requires.append('setuptools')
        return self.name_convert_deps_list(deps_from_pydit_json(run_requires))

    @property
    def build_deps(self):
        build_requires = self.get_requires(['build_requires', 'test_requires'])
        if 'setuptools' not in build_requires:
            build_requires.append('setuptools')
        return self.name_convert_deps_list(deps_from_pydit_json(build_requires, runtime=False))

    @property
    def py_modules(self):
        return self.archive.record.get('modules')

    @property
    def scripts(self):
        return self.archive.record.get('scripts', [])

    @property
    def home_page(self):
        urls = [url for url in self.json_metadata.get('extensions', {})
                                                 .get('python.details', {})
                                                 .get('project_urls', {}).values()]
        if urls:
            return urls[0]

    @property
    @process_description
    def description(self):
        return self.archive.wheel_description()

    @property
    def summary(self):
        return self.json_metadata.get('summary', None)

    @property
    def classifiers(self):
        return self.json_metadata.get('classifiers', [])

    @property
    def license(self):
        return self.json_metadata.get('license', None)

    @property
    def versions_from_archive(self):
        py_vers = utils.versions_from_trove(self.classifiers)
        return (py_vers[0] if py_vers else settings.DEFAULT_PYTHON_VERSION,
                py_vers[1:] if py_vers else [settings.DEFAULT_ADDITIONAL_VERSION])

    @property
    def has_test_suite(self):
        return self.json_metadata.get('test_requires', False) is not False

    @property
    def doc_files(self):
        return set([doc for doc in self.json_metadata.get('extensions', {})
                                                     .get('python.details', {})
                                                     .get('document_names', {}).values()])
