import os
import urllib
import xmlrpclib

class Downloader(object):
    def __init__(name, version = None, save_dir = None, server = 'http://pypi.python.org/pypi'):
        self.name = name
        self.version = version
        self.save_dir = save_dir or os.path.expanduser('~/rpmbuild/SOURCES/')
        self.server = server
        self.client = xmlrpmlib.ServerProxy(self.server)
        # TODO: verify that server is ok and package exists

    @property
    def url(self):
        if not self.version:
            self.version = self.client.package_releases(self.name)[0]

        return self.client.release_urls(self.name, self.version)[0]['url']

    def download(self):
        save_file = '%s/%s' % (self.save_dir, self.url.split('/')[-1])
        urllib.urlretrieve(self.url, save_file)
        return save_file
