import os
import glob
import logging
from virtualenvapi.manage import VirtualEnvironment
import virtualenvapi.exceptions as ve

from pyp2rpm.exceptions import VirtualenvFailException
from pyp2rpm.settings import DEFAULT_PYTHON_VERSION

logger = logging.getLogger(__name__)


def site_packages_filter(site_packages_list):
    '''Removes wheel .dist-info files'''
    return set([x for x in site_packages_list if not x.split('.')[-1] == 'dist-info'])

def deps_package_filter(deps_list, package):
    '''
    Removes package name from all installed packages to
    get dependencies
    '''
    return [x for x in deps_list if not x[0].lower() == package.lower()]

def deps_wheel_filter(deps_list):
    '''
    Removes wheel package from list of installed packages
    '''
    return [x for x in deps_list if not x[0] == 'wheel']

def scripts_filter(scripts):
    '''
    Removes .pyc files from scripts
    '''
    return [x for x in scripts if not x.split('.')[-1] == 'pyc']

class DirsContent(object):
    '''
    Object to store and compare directory content before and
    after instalation of package.
    '''
    def __init__(self, bindir=None, lib_sitepackages=None):
        self.bindir = bindir
        self.lib_sitepackages = lib_sitepackages

    def fill(self, path):
        '''
        Scans content of directories
        '''
        self.bindir = set(os.listdir(path + 'bin/'))
        self.lib_sitepackages = set(os.listdir(glob.glob(path + 'lib/python?.?/site-packages/')[0]))

    def __sub__(self, other):
        '''
        Makes differance of DirsContents objects attributes
        '''
        if any([self.bindir == None, self.lib_sitepackages == None,
                other.bindir == None, other.lib_sitepackages == None]):
            raise ValueError("Some of the attributes is uninicialized")
        result = DirsContent(
            self.bindir - other.bindir,
            self.lib_sitepackages - other.lib_sitepackages)
        return result


class VirtualEnv(object):

    def __init__(self, name, temp_dir, name_convertor, base_python_version):
        self.name = name
        self.temp_dir = temp_dir
        self.name_convertor = name_convertor
        if not base_python_version:
            base_python_version = DEFAULT_PYTHON_VERSION
        python_version = 'python' + base_python_version
        self.env = VirtualEnvironment(temp_dir + '/venv', python=python_version)
        try:
            self.env.open_or_create()
        except (ve.VirtualenvCreationException, ve.VirtualenvReadonlyException):
            logger.error('Failed to create virtualenv')
            raise VirtualenvFailException('Failed to create virtualenv')
        self.dirs_before_install = DirsContent()
        self.dirs_after_install = DirsContent()
        self.dirs_before_install.fill(temp_dir + '/venv/')
        self.installed_deps = []
        self.data = {}

    def install_package_to_venv(self):
        '''
        Installs package given as first argument to virtualenv using pip
        '''
        try:
            self.env.install(self.name)
        except (ve.PackageInstallationException, ve.VirtualenvReadonlyException):
            logger.error('Failed to install package to virtualenv')
            raise VirtualenvFailException('Failed to install package to virtualenv')

    def uninstall_deps_from_venv(self):
        '''
        Removes all dependencies from virtualenv and scans contents of
        directories
        '''
        try:
            for dep in self.installed_deps:
                self.env.uninstall(dep)
        except ve.PackageRemovalException:
            logger.error('Failed to uninstall some of runtime_deps packages')
            raise VirtualenvFailException('Failed to uninstall some of runtime_deps packages')
        self.dirs_after_install.fill(self.temp_dir + '/venv/')

    def change_deps_format(self, deps_list):
        '''
        Changes format of runtime deps to match format of archive
        data runtime deps
        '''
        if not deps_list:
            return []
        formated_deps = []
        for dep in deps_list:
            name = self.name_convertor.rpm_name(dep[0])
            formated_deps.append(['Requires', name.lower()])
        return formated_deps

    @property
    def get_pip_freeze(self):
        '''
        Gets all packages installed to venv, filters package name and wheel
        to get real dependancies
        '''
        pip_freeze = self.env.installed_packages
        self.installed_deps = deps_package_filter(pip_freeze, self.name)
        runtime_deps = self.change_deps_format(deps_wheel_filter(self.installed_deps))
        logger.debug('Runtime dependancies from pip freeze: {0}.'.format(runtime_deps))
        return runtime_deps

    @property
    def get_dirs_differance(self):
        '''
        Makes final versions of site_packages and scripts using DirsContent
        sub method and filters
        '''
        try:
            diff = self.dirs_after_install - self.dirs_before_install
        except ValueError:
            raise VirtualenvFailException("Some of the DirsContent attributes is uninicialized")
        site_packages = site_packages_filter(diff.lib_sitepackages)
        logger.debug('Site_packages from files differance in virtualenv: {0}.'.format(
            site_packages))
        scripts = scripts_filter(list(diff.bindir))
        logger.debug('Scripts from files differance in virtualenv: {0}.'.format(scripts))
        return (site_packages, scripts)

    @property
    def get_venv_data(self):
        try:
            self.install_package_to_venv()
            self.data['runtime_deps'] = self.get_pip_freeze
            self.uninstall_deps_from_venv()
            self.data['packages'], self.data['scripts'] = self.get_dirs_differance
        except VirtualenvFailException:
            logger.error("Skipping virtualenv metadata extraction")
        return self.data
