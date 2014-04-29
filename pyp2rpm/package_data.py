import subprocess
import time
import locale
import logging

from pyp2rpm import version

logger = logging.getLogger(__name__)


class PackageData():
    credit_line = '# Created by pyp2rpm-{0}'.format(version.version)

    """A simple object that carries data about a package."""

    def __init__(self, local_file, name, pkg_name, version, md5='', url=''):
        object.__setattr__(self, 'data', {})
        self.data['local_file'] = local_file
        self.data['name'] = name
        self.data['pkg_name'] = pkg_name
        self.data['version'] = version
        self.data['python_versions'] = []
        self.data['md5'] = md5
        self.data['url'] = url
        self.data['sphinx_dir'] = None

    def __getattr__(self, name):
        if name == 'underscored_name':
            return self.data['name'].replace('-', '_')
        elif name == 'changelog_date_packager':
            return self.get_changelog_date_packager()
        return self.data.get(name, 'TODO:')

    def __setattr__(self, name, value):
        if name == 'summary':
            value = value.rstrip('.').replace('\n', ' ')
        self.data[name] = value

    def set_from(self, data_dict):
        for k, v in data_dict.items():
            setattr(self, k, v)

    def get_changelog_date_packager(self):
        """Returns part of the changelog entry, containing date and packager.
        """
        try:
            packager = subprocess.Popen(
                'rpmdev-packager', stdout=subprocess.PIPE).communicate()[0].strip()
        except (OSError, FileNotFoundError):
            # Hi John Doe, you should install rpmdevtools
            packager = "John Doe <john@doe.com>"
            logger.warn(
                'Package rpmdevtools is missing, using default name: {0}'.format(packager))
        date_str = time.strftime('%a %b %d %Y', time.gmtime())
        encoding = locale.getpreferredencoding()
        return '{0} {1}'.format(date_str, packager.decode(encoding))
