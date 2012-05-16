import subprocess
import time

from pyp2rpmlib import utils

class PackageData(object):
    def __init__(self, local_file, name, version):
        self.local_file = local_file
        self.name = name
        self.version = version

    def __getattr__(self, name):
        if name in self.__dict__:
            return self.__dict__[name]

        return 'TODO:'

    @property
    def summary(self):
        return self._summary

    @summary.setter
    def summary(self, value):
        self._summary = value.rstrip('.')

    @property
    def pkg_name(self):
        utils.rpm_name(self.name)

    @property
    def changelog_date_packager(self):
        packager = subprocess.Popen('rpmdev-packager', stdout = subprocess.PIPE).communicate()[0].strip()
        date_str = time.strftime('%a %b %d %Y', time.gmtime())
        return "%s %s" % (date_str, packager)

class PypiData(PackageData):
    def __init__(self, local_file, name, version, md5, url):
        super(PypiData, self).__init__(local_file, name, version)
        self.md5 = md5
        self.url = url

class LocalData(PackageData):
    def __init__(self, local_file, name, version):
        super(LocalData, self).__init__(local_file, name, version)
