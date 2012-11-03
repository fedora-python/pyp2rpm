import os
import shutil
try:
    import urllib.request as request
except ImportError:
    import urllib as request
try:
    import xmlrpclib
except ImportError:
    import xmlrpc.client as xmlrpclib

from pyp2rpm import settings
from pyp2rpm import exceptions

class PackageGetter(object):
    """Base class for package getters"""
    def get(self):
        raise NotImplementedError('Whoops, get method not implemented by {0}.'.format(self.__class__))

    def get_name_version(self):
        """Returns (name, version) tuple.
        Returns:
            (name, version) tuple of the package.
        """
        raise NotImplementedError('Whoops, get method not implemented by {0}.'.format(self.__class__))

class PypiDownloader(PackageGetter):
    """Class for downloading the package from PyPI."""
    def __init__(self, client, name, version = None, save_dir = None):
        self.client = client
        self.name = name
        try:
            self.version = version or self.client.package_releases(self.name)[0]
        except IndexError: # no such package
            raise exceptions.NoSuchPackageException('Package "{0}" could not be found on PyPI.'.format(name))
        if version and self.client.release_urls(name, version) == []: # if version is specified, will check if such version exists
            raise exceptions.NoSuchPackageException('Package with name "{0}" and version "{1}" could not be found on PyPI'.format(name, version))
        self.save_dir = save_dir or settings.DEFAULT_PKG_SAVE_PATH

    @property
    def url(self):
        urls = self.client.release_urls(self.name, self.version)
        if len(urls) > 0:
            return self.client.release_urls(self.name, self.version)[0]['url']
        else:
            return self.client.release_data(self.name, self.version)['download_url']


    def get(self):
        """Downloads the package from PyPI.
        Returns:
            Full path of the downloaded file.
        Raises:
            EnvironmentError if the save_dir is not writable.
        """
        save_file = '{0}/{1}'.format(self.save_dir, self.url.split('/')[-1])
        request.urlretrieve(self.url, save_file)
        return save_file

    def get_name_version(self):
        return (self.name, self.version)

class LocalFileGetter(PackageGetter):
    def __init__(self, local_file, save_dir = None):
        self.local_file = local_file
        self.save_dir = save_dir or settings.DEFAULT_PKG_SAVE_PATH

    def get(self):
        """Copies file from local filesystem to self.save_dir.
        Returns:
            Full path of the copied file.
        Raises:
            EnvironmentError if the file can't be found or the save_dir is not writable.
        """
        save_file = '{0}/{1}'.format(self.save_dir, os.path.basename(self.local_file))
        if not os.path.exists(save_file) or not os.path.samefile(self.local_file, save_file):
            shutil.copy2(self.local_file, save_file)

        return save_file

    @property
    def _stripped_name_version(self):
        """Returns filename stripped of the suffix.
        Returns:
            Filename stripped of the suffix (extension).
        """
        # we don't use splitext, because on "a.tar.gz" it returns ("a.tar", "gz")
        filename = os.path.basename(self.local_file)
        for archive_suffix in settings.ARCHIVE_SUFFIXES:
            if filename.endswith(archive_suffix):
                return filename.rstrip('{0}'.format(archive_suffix))

        raise exceptions.UnknownArchiveFormatException('Unkown archive format of file {0}.'.format(filename))

    def get_name_version(self):
        split_name_version = self._stripped_name_version.rsplit('-', 2)
        if len(split_name_version) == 3:
            if not split_name_version[2].startswith('py'):
                split_name_version[0] = '-'.join(split_name_version[0:2])
                split_name_version[1] = split_name_version[2]

        return (split_name_version[0], split_name_version[1])
