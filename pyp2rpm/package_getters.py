import logging
import os
import shutil
import subprocess
import tempfile
import shutil
import re
try:
    import urllib.request as request
except ImportError:
    import urllib as request

from pyp2rpm import settings
from pyp2rpm import exceptions


logger = logger = logging.getLogger(__name__)


class PackageGetter(object):

    """Base class for package getters"""

    def get(self):
        pass

    def get_name_version(self):
        """Returns (name, version) tuple.
        Returns:
            (name, version) tuple of the package.
        """
        pass

    def __del__(self):
        if hasattr(self, "temp_dir"):
            shutil.rmtree(self.temp_dir)


class PypiDownloader(PackageGetter):

    """Class for downloading the package from PyPI."""

    def __init__(self, client, name, version=None, save_dir=None):
        self.client = client
        self.name = name
        self.versions = self.client.package_releases(self.name)
        if not self.versions:  # If versions is empty list then there is no such package on PyPI
            raise exceptions.NoSuchPackageException(
                'Package "{0}" could not be found on PyPI.'.format(name))
            logger.error('Package "{0}" could not be found on PyPI.'.format(name))

        self.version = version or self.versions[0]

        # if version is specified, will check if such version exists
        if version and self.client.release_urls(name, version) == []:
            raise exceptions.NoSuchPackageException(
                'Package with name "{0}" and version "{1}" could not be found on PyPI.'.format(
                    name, version))
            logger.error(
                'Package with name "{0}" and version "{1}" could not be found on PyPI.'.format(
                    name, version))

        self.save_dir = save_dir or settings.DEFAULT_PKG_SAVE_PATH
        if self.save_dir == settings.DEFAULT_PKG_SAVE_PATH:
            self.save_dir += '/SOURCES'

        if not os.path.exists(self.save_dir):
            if self.save_dir != (settings.DEFAULT_PKG_SAVE_PATH + '/SOURCES'):
                os.makedirs(self.save_dir)
            else:
                try:
                    subprocess.Popen(
                        'rpmdev-setuptree', stdout=subprocess.PIPE)
                    logger.info('Using rpmdevtools package to make rpmbuild folders tree.')
                except OSError:
                    self.save_dir = '/tmp'  # pyp2rpm can work without rpmdevtools
                    logger.warn('Package rpmdevtools is missing , using default folder: '
                                '{0} to store {1}.'.format(self.save_dir, self.name))
                    logger.warn('Specify folder to store a file (SAVE_DIR) or install rpmdevtools.')
        logger.info('Using {0} as directory to save source.'.format(self.save_dir))

        self.temp_dir = tempfile.mkdtemp()

    def url(self, wheel=False):
        urls = self.client.release_urls(self.name, self.version)
        if not wheel:
            if urls:
                zip_url = ''
                for url in urls:
                    if url['url'].endswith((".tar.gz")):
                        return url['url']
                    if url['url'].endswith((".zip")):
                        zip_url = url['url']
                return zip_url or urls[0]['url']
            return self.client.release_data(self.name, self.version)['release_url']
        else:
            for url in urls:
                if url['url'].endswith("none-any.whl"):
                    return url['url']
            return None

    def get(self, wheel=False):
        """Downloads the package from PyPI.
        Returns:
            Full path of the downloaded file.
        Raises:
            PermissionError if the save_dir is not writable.
        """
        url = self.url(wheel)
        if not url:
            return None
        if wheel:
            save_dir = self.temp_dir
        else:
            save_dir = self.save_dir

        save_file = '{0}/{1}'.format(save_dir, url.split('/')[-1])
        request.urlretrieve(url, save_file)
        logger.info('Downloaded package from PyPI: {0}.'.format(save_file))
        return save_file

    def get_name_version(self):
        return (self.name, self.version)


class LocalFileGetter(PackageGetter):

    def __init__(self, local_file, save_dir=None):
        self.local_file = local_file
        self.save_dir = save_dir or settings.DEFAULT_PKG_SAVE_PATH
        if self.save_dir == settings.DEFAULT_PKG_SAVE_PATH:
            self.save_dir += '/SOURCES'

        self.name_version_pattern = re.compile("(^.*?)-(\d+\.?\d*\.?\d*\.?\d*).*$")

        if not os.path.exists(self.save_dir):
            if self.save_dir != settings.DEFAULT_PKG_SAVE_PATH:
                os.makedirs(self.save_dir)
            else:
                try:
                    subprocess.Popen(
                        'rpmdev-setuptree', stdout=subprocess.PIPE)
                    logger.info('Using rpmdevtools package to make rpmbuild folders tree.')
                except OSError:
                    self.save_dir = '/tmp'  # pyp2rpm can work without rpmdevtools
                    logger.warn('Package rpmdevtools is missing , using default folder: {0} to store {1}.'.format(
                        self.save_dir, self.local_file))
                    logger.warn('Specify folder to store a file or install rpmdevtools.')

        self.temp_dir = tempfile.mkdtemp()

    def get(self):
        """Copies file from local filesystem to self.save_dir.
        Returns:
            Full path of the copied file.
        Raises:
            EnvironmentError if the file can't be found or the save_dir is not writable.
        """
        if self.local_file.endswith('.whl'):
            save_dir = self.temp_dir
        else:
            save_dir = self.save_dir

        save_file = '{0}/{1}'.format(save_dir, os.path.basename(self.local_file))
        if not os.path.exists(save_file) or not os.path.samefile(self.local_file, save_file):
            shutil.copy2(self.local_file, save_file)
        logger.info('Local file: {0} copyed to {1}.'.format(self.local_file, save_file))

        return save_file

    @property
    def _stripped_name_version(self):
        """Returns filename stripped of the suffix.
        Returns:
            Filename stripped of the suffix (extension).
        """
        # we don't use splitext, because on "a.tar.gz" it returns ("a.tar",
        # "gz")
        filename = os.path.basename(self.local_file)
        for archive_suffix in settings.ARCHIVE_SUFFIXES:
            if filename.endswith(archive_suffix):
                return filename.rstrip('{0}'.format(archive_suffix))
        # if for cycle is exhausted it means no suffix was found
        else:
            raise exceptions.UnknownArchiveFormatException(
                'Unkown archive format of file {0}.'.format(filename))
            logger.error(
                'Unkown archive format of file {0}.'.format(filename), exc_info=True)
            logger.info('Rpmbuild failed. See log for more info.')

    def get_name_version(self):
        name, version = self.name_version_pattern.search(self._stripped_name_version).groups()
        if version[-1] == '.':
            version = version[:-1]
        return (name, version)
