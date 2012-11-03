import subprocess
import time
import locale

from pyp2rpm import version

class PackageData(object):
    credit_line = '# Created by pyp2rpm-{0}'.format(version.version)

    """A simple object that carries data about a package."""
    def __init__(self, local_file, name, pkg_name, version):
        self.local_file = local_file
        self.name = name
        self.pkg_name = pkg_name
        self.version = version
        self.python_versions = []
        self._sphinx_dir = None

    def __getattr__(self, name):
        if name in self.__dict__:
            return self.__dict__[name]

        return 'TODO:'

    def set_from(self, data_dict):
        for k, v in data_dict.items():
            setattr(self, k, v)

    @property
    def summary(self):
        return self._summary

    @summary.setter
    def summary(self, value):
        self._summary = value.rstrip('.')

    @property
    def sphinx_dir(self):
        return self._sphinx_dir

    @sphinx_dir.setter
    def sphinx_dir(self, value):
        self._sphinx_dir = value

    @property
    def underscored_name(self):
        return self.name.replace('-', '_')

    @property
    def changelog_date_packager(self):
        """Returns part of the changelog entry, containing date and packager.
        """
        packager = subprocess.Popen('rpmdev-packager', stdout = subprocess.PIPE).communicate()[0].strip()
        date_str = time.strftime('%a %b %d %Y', time.gmtime())
        encoding = locale.getpreferredencoding()
        return '{0} {1}'.format(date_str, packager.decode(encoding))

class PypiData(PackageData):
    """Carries data about package from PyPI"""
    def __init__(self, local_file, name, pkg_name, version, md5, url):
        super(PypiData, self).__init__(local_file, name, pkg_name, version)
        self.md5 = md5
        self.url = url

class LocalData(PackageData):
    def __init__(self, local_file, name, pkg_name, version):
        super(LocalData, self).__init__(local_file, name, pkg_name, version)
