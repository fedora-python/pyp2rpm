from abc import ABCMeta, abstractmethod
import logging
import os
import shutil
import subprocess
import urllib.request as request
import xmlrpc.client as xmlrpclib

from pyp2rpm import settings
from pyp2rpm import exceptions

logger = logger = logging.getLogger(__name__)


class PackageGetter(metaclass=ABCMeta):

    """Base class for package getters"""

    @abstractmethod
    def get(self):
        pass

    @abstractmethod
    def get_name_version(self):
        """Returns (name, version) tuple.
        Returns:
            (name, version) tuple of the package.
        """


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

        if version and self.client.release_urls(name, version) == []:  # if version is specified, will check if such version exists
            raise exceptions.NoSuchPackageException(
                'Package with name "{0}" and version "{1}" could not be found on PyPI'.format(name, version))
            logger.error('Package with name "{0}" and version "{1}" could not be found on PyPI'.format(name, version))

        self.save_dir = save_dir or settings.DEFAULT_PKG_SAVE_PATH

        if not os.path.exists(self.save_dir):
            if self.save_dir != settings.DEFAULT_PKG_SAVE_PATH:
                os.makedirs(self.save_dir)
            else:
                try:
                    subprocess.Popen(
                        'rpmdev-setuptree', stdout=subprocess.PIPE)
                    logger.info('Using rpmdevtools package to make rpmbuild folders tree')
                except (OSError, FileNotFoundError):
                    self.save_dir = '/tmp'  # pyp2rpm can work without rpmdevtools
                    logger.warn('Package rpmdevtools is missing , using default folder: {0} to store {1}'.format(
                        self.save_dir, self.local_file))
                    logger.warn('Specify folder to store a file or install rpmdevtools')

    @property
    def url(self):
        urls = self.client.release_urls(self.name, self.version)
        for url in urls:
            if url['url'].endswith(".tar.gz"):
                return url['url']
        return urls[0]['url']

    def get(self):
        """Downloads the package from PyPI.
        Returns:
            Full path of the downloaded file.
        Raises:
            PermissionError if the save_dir is not writable.
        """
        save_file = '{0}/{1}'.format(self.save_dir, self.url.split('/')[-1])
        request.urlretrieve(self.url, save_file)
        return save_file

    def get_name_version(self):
        return (self.name, self.version)


class LocalFileGetter(PackageGetter):

    def __init__(self, local_file, save_dir=None):
        self.local_file = local_file
        self.save_dir = save_dir or settings.DEFAULT_PKG_SAVE_PATH

        if not os.path.exists(self.save_dir):
            if self.save_dir != settings.DEFAULT_PKG_SAVE_PATH:
                os.makedirs(self.save_dir)
            else:
                try:
                    subprocess.Popen(
                        'rpmdev-setuptree', stdout=subprocess.PIPE)
                    logger.info('Using rpmdevtools package to make rpmbuild folders tree')
                except (OSError, FileNotFoundError):
                    self.save_dir = '/tmp'  # pyp2rpm can work without rpmdevtools
                    logger.warn('Package rpmdevtools is missing , using default folder: {0} to store {1}'.format(
                        self.save_dir, self.local_file))
                    logger.warn('Specify folder to store a file or install rpmdevtools')

    def get(self):
        """Copies file from local filesystem to self.save_dir.
        Returns:
            Full path of the copied file.
        Raises:
            FileNotFoundError if the file can't be found
            PermissionError if the save_dir is not writable.
        """
        save_file = '{0}/{1}'.format(
            self.save_dir, os.path.basename(self.local_file))
        if not os.path.exists(save_file) or not os.path.samefile(self.local_file, save_file):
            shutil.copy2(self.local_file, save_file)

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
            log.error(
                'Unkown archive format of file {0}.'.format(filename), exc_info=True)
            log.info("That's all folks!")

    def get_name_version(self):
        split_name_version = self._stripped_name_version.rsplit('-', 2)
        if len(split_name_version) == 3:
            if not split_name_version[2].startswith('py'):
                split_name_version[0] = '-'.join(split_name_version[0:2])
                split_name_version[1] = split_name_version[2]

        return (split_name_version[0], split_name_version[1])
