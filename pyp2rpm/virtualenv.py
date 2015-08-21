import os
from subprocess import Popen, PIPE

from pyp2rpm.settings import VENV_INTERPRETER

PYTHON_VERSION = VENV_INTERPRETER.split('/')[-1]

def site_packages_filter(site_packages_list):
    '''Removes wheel .dist-info files'''
    return [x for x in site_packages_list if not x.split('.')[-1] == 'dist-info']
    
def deps_package_filter(deps_list, package):
    '''
    Removes package name from all installed packages to 
    get dependencies
    '''
    return [x for x in deps_list if not x.split('==')[0].lower() == package.lower()]

def deps_wheel_filter(deps_list):
    return [x for x in deps_list if not x.split('==')[0] == 'wheel']

def change_deps_format(deps_list):
    '''
    Changes format of runtime deps to match format of archive 
    data runtime deps
    '''
    formated_deps = []
    for dep in deps_list:
        name, version = dep.split('==')
    formated_deps.append(['Requires', name, '>=', version]) # TODO name_convertor
    return formated_deps


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

    def __init__(self, name, temp_dir):
        self.name = name
        self.temp_dir = temp_dir
        self.create_virtualenv()
        self.dirs_before_install = DirsContent()
        self.dirs_after_install = DirsContent()
        self.dirs_before_install.fill(self.temp_dir + '/venv/')
        self.data = {}

    def create_virtualenv(self):
        '''
        Creates new virtualenv in temp_dir
        '''
        proc = Popen(['virtualenv', '-p', VENV_INTERPRETER, self.temp_dir + '/venv/'], stdout=PIPE)
        proc.communicate()
        if proc.returncode != 0:
            pass # TODO error handle output to log??

    def install_package_to_venv(self):
        '''
        Installs package given as first argument to virtualenv
        '''
        proc = Popen([self.temp_dir + "/venv/bin/pip", "install", "--egg", self.name], stdout=PIPE)
        proc.communicate()
        if proc.returncode != 0:
            pass # TODO error handle

    def uninstall_deps_from_venv(self):
        '''
        Removes all dependencies from virtualenv to get only files of packages
        '''
        proc = Popen([self.temp_dir + "/venv/bin/pip", "uninstall", "-y"] + self.installed_deps, stdout=PIPE)
        proc.communicate()
        if proc.returncode != 0:
            pass # TODO handle error
        self.dirs_after_install.fill(self.temp_dir + '/venv/')

    def get_pip_freeze(self):
        '''
        Gets all packages installed to venv using pip freeze, filters package
        name and wheel to get real dependancies
        '''
        proc = Popen([self.temp_dir + '/venv/bin/pip', 'freeze'], stdout=PIPE)
        pip_freeze = proc.stdout.read().decode('utf-8').splitlines()
        self.installed_deps = deps_package_filter(pip_freeze, self.name)
        self.data['runtime_deps'] = change_deps_format(deps_wheel_filter(self.installed_deps))

    def get_dirs_differance(self):
        diff =  self.dirs_after_install - self.dirs_before_install
        self.data['site_packages'] = site_packages_filter(diff.lib_sitepackages)
        self.data['scripts'] = list(diff.bindir)

    @property
    def get_venv_data(self):
        self.install_package_to_venv()
        self.get_pip_freeze()
        self.uninstall_deps_from_venv()
        self.get_dirs_differance()
        return self.data
