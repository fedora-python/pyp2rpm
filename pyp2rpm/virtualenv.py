import os
import logging
import locale
from subprocess import Popen, PIPE, DEVNULL

from pyp2rpm.settings import VENV_INTERPRETER

logger = logging.getLogger(__name__)

PYTHON_VERSION = VENV_INTERPRETER.split('/')[-1]

def site_packages_filter(site_packages_list):
    '''Removes wheel .dist-info files'''
    return {x for x in site_packages_list if not x.split('.')[-1] == 'dist-info'}
    
def deps_package_filter(deps_list, package):
    '''
    Removes package name from all installed packages to 
    get dependencies
    '''
    return [x for x in deps_list if not x.split('==')[0].lower() == package.lower()]

def deps_wheel_filter(deps_list):
    return [x for x in deps_list if not x.split('==')[0] == 'wheel']



class DirsContent(object):
    '''
    Object to store and compare directory content before and 
    after instalation.
    '''
    def __init__(self, bindir=set(), lib_sitepackages=set(), lib64_sitepackages=set()):
        self.bindir = bindir
        self.lib_sitepackages = lib_sitepackages

    def fill(self, path):
        '''
        Scans content of directories
        '''
        self.bindir = set(os.listdir(path + 'bin/'))
        self.lib_sitepackages = set(os.listdir(path + 'lib/' + PYTHON_VERSION + '/site-packages/'))
    
    def __sub__(self, other):
       '''
       Makes differance of DirsContents objects attributes
       '''
       result = DirsContent(
           self.bindir - other.bindir,
           self.lib_sitepackages - other.lib_sitepackages)
       return result


class VirtualEnv(object):

    def __init__(self, name, temp_dir, name_convertor):
        self.name = name
        self.temp_dir = temp_dir
        self.name_convertor = name_convertor
        self.venv_install_error = False
        if not self.create_virtualenv():
            self.venv_install_error = True
        self.dirs_before_install = DirsContent()
        self.dirs_after_install = DirsContent()
        self.dirs_before_install.fill(self.temp_dir + '/venv/')
        self.data = {}

    def create_virtualenv(self):
        '''
        Creates new virtualenv in temp_dir
        '''
        proc = Popen(['virtualenv', '-p', VENV_INTERPRETER, self.temp_dir + '/venv/'], 
                stdout=DEVNULL, stderr=PIPE)
        proc.communicate()
        if proc.returncode != 0:
            logger.error('{0}skipping venv matadata extraction.'.format(
                proc.stderr.read().decode(locale.getpreferredencoding())))
            return False
        return True

    def install_package_to_venv(self):
        '''
        Installs package given as first argument to virtualenv
        '''
        proc = Popen([self.temp_dir + "/venv/bin/pip", "install", "--egg", self.name], 
                stdout=DEVNULL, stderr=PIPE)
        proc.communicate()
        if proc.returncode != 0:
            logger.error('pip failed to install package: {0}skipping venv'
                    ' metadata extraction.'.format(proc.stderr.read().decode(locale.getpreferredencoding())))
            return False
        return True

    def uninstall_deps_from_venv(self):
        '''
        Removes all dependencies from virtualenv to get only files of packages
        '''
        proc = Popen([self.temp_dir + "/venv/bin/pip", "uninstall", "-y"] + self.installed_deps, 
                stdout=DEVNULL, stderr=PIPE)
        proc.communicate()
        if proc.returncode != 0:
            logger.error('{0}skipping venv metadata extraction.'.format(
                proc.stderr.read().decode(locale.getpreferredencoding())))
            return False
        self.dirs_after_install.fill(self.temp_dir + '/venv/')
        return True

    def change_deps_format(self, deps_list):
        '''
        Changes format of runtime deps to match format of archive 
        data runtime deps
        '''
        if not deps_list:
            return []
        formated_deps = []
        for dep in deps_list:
            name, version = dep.split('==')      #TODO use version??
        name = self.name_convertor.rpm_name(name.lower())
        formated_deps.append(['Requires', name])
        return formated_deps

    @property
    def get_pip_freeze(self):
        '''
        Gets all packages installed to venv using pip freeze, filters package
        name and wheel to get real dependancies
        '''
        proc = Popen([self.temp_dir + '/venv/bin/pip', 'freeze'], stdout=PIPE)
        pip_freeze = proc.stdout.read().decode(locale.getpreferredencoding()).splitlines()
        self.installed_deps = deps_package_filter(pip_freeze, self.name)
        return  self.change_deps_format(deps_wheel_filter(self.installed_deps))

    @property
    def get_dirs_differance(self):
        diff =  self.dirs_after_install - self.dirs_before_install
        return (site_packages_filter(diff.lib_sitepackages),
                list(diff.bindir))

    @property
    def get_venv_data(self):
        if self.venv_install_error:
            return {}
        if not self.install_package_to_venv():
            return {}
        self.data['runtime_deps'] = self.get_pip_freeze
        if not self.uninstall_deps_from_venv():
            return self.data
        self.data['packages'], self.data['scripts'] = self.get_dirs_differance
        return self.data
