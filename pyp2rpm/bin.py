import argparse
import os
import locale

from pyp2rpm.convertor import Convertor
from pyp2rpm import settings

def main():
    parser = argparse.ArgumentParser(description = 'Convert PyPI package to RPM specfile.')
    parser.add_argument('-n',
                        required = False,
                        help = 'Name of the package on PyPI (ignored for local files).',
                        metavar = 'PYPI_NAME')
    parser.add_argument('-v',
                        required = False,
                        help = 'Version of the package to download (ignored for local files).',
                        metavar = 'VERSION')
    parser.add_argument('-m',
                        required = False,
                        help = 'Where to get metadata from ("pypi" or "local", default: "{0}").'.format(settings.DEFAULT_METADATA_SOURCE),
                        metavar = 'METADATA_SOURCE',
                        choices = ['pypi', 'local'],
                        default = settings.DEFAULT_METADATA_SOURCE)
    parser.add_argument('-s',
                        required = False,
                        help = 'Where to get package from ("pypi" or "/full/path/to/local/file", default: "{0}").'.format(settings.DEFAULT_PKG_SOURCE),
                        metavar = 'PACKAGE_SOURCE',
                        default = settings.DEFAULT_PKG_SOURCE)
    parser.add_argument('-d',
                        required = False,
                        help = 'Where to save the package file (default: "{0}")'.format(settings.DEFAULT_PKG_SAVE_PATH),
                        metavar = 'SAVE_DIR',
                        default = settings.DEFAULT_PKG_SAVE_PATH)
    parser.add_argument('-t',
                        required = False,
                        help = 'Template file (jinja2 format) to render (default: "{0}"). Search order is 1) filesystem, 2) default templates.'.format(settings.DEFAULT_TEMPLATE),
                        metavar = 'TEMPLATE') # no default, because we need to know, whether this was specified or not
    parser.add_argument('-o',
                        required = False,
                        help = 'Default distro whose conversion rules to use (default: "{0}"). Default templates have their rules associated and ignore this.'.format(settings.DEFAULT_DISTRO),
                        metavar = 'DISTRO',
                        default = settings.DEFAULT_DISTRO,
                        choices = settings.KNOWN_DISTROS)
    parser.add_argument('-b',
                        required = False,
                        help = 'Base Python version to package for (default: "{0}").'.format(settings.DEFAULT_PYTHON_VERSION),
                        metavar = 'BASE_PYTHON',
                        default = settings.DEFAULT_PYTHON_VERSION)
    parser.add_argument('-p',
                        required = False,
                        help = 'Additional Python versions to include in the specfile (e.g -p3 for %%{?with_python3}). Can be specified multiple times.',
                        metavar = 'PYTHON_VERSION',
                        default = [],
                        action = 'append')


    ns = parser.parse_args()
    if ns.__dict__['n'] == None and not os.path.exists(ns.__dict__['s']):
        parser.error('You must specify name of the package (-n) or full path (-s).')

    distro = ns.__dict__['o']
    if ns.__dict__['t'] in settings.KNOWN_DISTROS:
        distro = ns.__dict__['t']

    convertor = Convertor(name = ns.__dict__['n'],
                          version = ns.__dict__['v'],
                          metadata_from = ns.__dict__['m'],
                          source_from = ns.__dict__['s'],
                          save_dir = ns.__dict__['d'],
                          template = ns.__dict__['t'] or settings.DEFAULT_TEMPLATE,
                          distro = distro,
                          base_python_version = ns.__dict__['b'],
                          python_versions = ns.__dict__['p'])

    converted = convertor.convert()

    if isinstance(converted, str): # python 3
        print(converted)
    else: # python 2
        print(converted.encode(locale.getpreferredencoding()))
