import subprocess
import time
import locale
import logging

from pyp2rpm import version
from pyp2rpm import utils

logger = logging.getLogger(__name__)


def get_deps_names(runtime_deps_list):
    '''
    data['runtime_deps'] has format:
    [['Requires', 'name', '>=', 'version'], ...]
    this function creates list of lowercase deps names
    '''
    return [x[1].lower() for x in runtime_deps_list]


class PackageData(object):
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
        elif name in ['runtime_deps', 'build_deps', 'classifiers', 'doc_files', 'doc_license']:
            return self.data.get(name, [])
        elif name in ['packages', 'py_modules', 'scripts']:
            return self.data.get(name, set())
        elif name in ['has_egg_info', 'has_test_suite', 'has_pth', 'has_extension']:
            return self.data.get(name, False)
        return self.data.get(name, 'TODO:')

    def __setattr__(self, name, value):
        if name == 'summary' and isinstance(value, utils.str_classes):
            value = value.rstrip('.').replace('\n', ' ')
        if value is not None:
            self.data[name] = value

    def update_attr(self, name, value):
        if name in self.data and value:
            if name in ['runtime_deps', 'build_deps']:  # compare lowercase names of deps
                for item in value:
                    if not item[1].lower() in get_deps_names(self.data[name]):
                        self.data[name].append(item)
            elif isinstance(self.data[name], list):
                for item in value:
                    if item not in self.data[name]:
                        self.data[name].append(item)
            elif isinstance(self.data[name], set):
                if not isinstance(value, set):
                    value = set(value)
                self.data[name] |= value
            elif not self.data[name] and self.data[name] is not False:
                self.data[name] = value
        elif name not in self.data and value is not None:
            self.data[name] = value

    def set_from(self, data_dict, update=False):
        for k, v in data_dict.items():
            if update:
                self.update_attr(k, v)
            else:
                setattr(self, k, v)

    def get_changelog_date_packager(self):
        """Returns part of the changelog entry, containing date and packager.
        """
        try:
            packager = subprocess.Popen(
                'rpmdev-packager', stdout=subprocess.PIPE).communicate()[0].strip()
        except OSError:
            # Hi John Doe, you should install rpmdevtools
            packager = "John Doe <john@doe.com>"
            logger.warn(
                'Package rpmdevtools is missing, using default name: {0}.'.format(packager))
        date_str = time.strftime('%a %b %d %Y', time.gmtime())
        encoding = locale.getpreferredencoding()
        return u'{0} {1}'.format(date_str, packager.decode(encoding))
