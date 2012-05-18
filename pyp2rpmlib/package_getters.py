import os
import shutil
import urllib
import xmlrpclib

from pyp2rpmlib import settings
from pyp2rpmlib import exceptions

class PackageGetter(object):
    """Base class for package getters"""
    def get(self):
        raise NotImplementedError('Whoops, get method not implemented by %s.' % self.__class__)

    def get_name_version(self):
        """Returns (name, version) tuple.
        Returns:
            (name, version) tuple of the package.
        """
        raise NotImplementedError('Whoops, get method not implemented by %s.' % self.__class__)

class PypiDownloader(PackageGetter):
    """Class for downloading the package from PyPI."""
    def __init__(self, client, name, version = None, save_dir = None):
        self.client = client
        self.name = name
        self.version = version or self.client.package_releases(self.name)[0]
        self.save_dir = save_dir or settings.DEFAULT_PKG_SAVE_PATH
        # TODO: verify that package exists

    @property
    def url(self):
        return self.client.release_urls(self.name, self.version)[0]['url']

    def get(self):
        """Downloads the package from PyPI.
        Returns:
            Full path of the downloaded file.
        Raises:
            EnvironmentError if the save_dir is not writable.
        """
        save_file = '%s/%s' % (self.save_dir, self.url.split('/')[-1])
        urllib.urlretrieve(self.url, save_file)
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
        save_file = '%s/%s' % (self.save_dir, os.path.basename(self.local_file))
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
                return filename.rstrip("%s" % archive_suffix)

        raise exceptions.UnknownArchiveFormatException('Unkown archive format of file %s.' % filename)

    def get_name_version(self):
        split_name_version = self._stripped_name_version.rsplit('-', 2)

        return (split_name_version[0], split_name_version[1])
