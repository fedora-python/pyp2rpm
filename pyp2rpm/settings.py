from pyp2rpm import utils

DEFAULT_TEMPLATE = 'fedora'
DEFAULT_PYTHON_VERSIONS = {
    'fedora': ['3'],
    'epel7': ['2', '3'],
    'epel6': ['2'],
    'mageia': ['3'],
    'pld': ['2', '3']
}
DEFAULT_PYTHON_VERSION = DEFAULT_PYTHON_VERSIONS[DEFAULT_TEMPLATE][0]
DEFAULT_PKG_SOURCE = 'pypi'
DEFAULT_METADATA_SOURCE = 'pypi'
DEFAULT_DISTRO = 'fedora'
DEFAULT_PKG_SAVE_PATH = utils.get_default_save_path()
KNOWN_DISTROS = DEFAULT_PYTHON_VERSIONS.keys()
ARCHIVE_SUFFIXES = ['.tar', '.tgz', '.tar.gz', '.tar.bz2',
                    '.gz', '.bz2', '.xz', '.zip', '.egg', '.whl']
EXTENSION_SUFFIXES = ['.c', '.cpp']
MODULE_SUFFIXES = ('.py', '.pyc')
DOC_FILES_RE = [r'readme.+', r'licens.+', r'copying.+']
LICENSE_FILES = ['license', 'copyright', 'copying']
SPHINX_DIR_RE = r'[^/]+/doc.?'
PYPI_URL = 'https://pypi.org/pypi'
PYPI_USABLE_DATA = ['description', 'summary', 'license',
                    'home_page', 'requires']
PYTHON_INTERPRETER = '/usr/bin/python'
EXTRACT_DIST_COMMAND_ARGS = ['--quiet', '--command-packages',
                             'pyp2rpm.command', 'extract_dist']
RPM_RICH_DEP_BLACKLIST = ['epel6', 'epel7']

TROVE_LICENSES = {
    'License :: OSI Approved :: Academic Free License (AFL)': 'AFL',
    'License :: OSI Approved :: Apache Software License': 'ASL %(TODO: version)s',
    'License :: OSI Approved :: Apple Public Source License': 'APSL %(TODO: version)s',
    'License :: OSI Approved :: Artistic License': 'Artistic %(TODO: version)s',
    'License :: OSI Approved :: Attribution Assurance License': 'AAL',
    'License :: OSI Approved :: BSD License': 'BSD',
    'License :: OSI Approved :: Common Public License': 'CPL',
    'License :: OSI Approved :: Eiffel Forum License': 'EFL %(TODO: version)s',
    'License :: OSI Approved :: European Union Public Licence 1.0 (EUPL 1.0)': 'EUPL 1.0',
    'License :: OSI Approved :: European Union Public Licence 1.1 (EUPL 1.1)': 'EUPL 1.1',
    'License :: OSI Approved :: GNU Affero General Public License v3': 'AGPLv3',
    'License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)': 'AGPLv3+',
    'License :: OSI Approved :: GNU Free Documentation License (FDL)': 'GFDL',
    'License :: OSI Approved :: GNU General Public License (GPL)': 'GPL',
    'License :: OSI Approved :: GNU General Public License v2 (GPLv2)': 'GPLv2',
    'License :: OSI Approved :: GNU General Public License v2 or later (GPLv2+)': 'GPLv2+',
    'License :: OSI Approved :: GNU General Public License v3 (GPLv3)': 'GPLv3',
    'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)': 'GPLv3+',
    'License :: OSI Approved :: GNU Lesser General Public License v2 (LGPLv2)': 'LGPLv2',
    'License :: OSI Approved :: GNU Lesser General Public License v2 or later (LGPLv2+)': 'LGPLv2+',
    'License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)': 'LGPLv3',
    'License :: OSI Approved :: GNU Lesser General Public License v3 or later (LGPLv3+)': 'LGPLv3+',
    'License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)': 'LGPL',
    'License :: OSI Approved :: IBM Public License': 'IBM',
    'License :: OSI Approved :: Intel Open Source License': 'Intel Open Source License - Deprecated (BAD)',
    'License :: OSI Approved :: ISC License (ISCL)': 'ISC',
    'License :: OSI Approved :: Jabber Open Source License': 'Jabber',
    'License :: OSI Approved :: MIT License': 'MIT',
    'License :: OSI Approved :: MITRE Collaborative Virtual Workspace License (CVW)': 'MITRE - Deprecated (BAD)',
    'License :: OSI Approved :: Motosoto License': 'Motosoto',
    'License :: OSI Approved :: Mozilla Public License 1.0 (MPL)': 'MPLv1.0',
    'License :: OSI Approved :: Mozilla Public License 1.1 (MPL 1.1)': 'MPLv1.1',
    'License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)': 'MPLv2.0',
    'License :: OSI Approved :: Nethack General Public License': 'NGPL',
    'License :: OSI Approved :: Nokia Open Source License': 'Nokia',
    'License :: OSI Approved :: Open Group Test Suite License': 'Open Group Test Suite License - Flawed (BAD)',
    'License :: OSI Approved :: Python License (CNRI Python License)': 'CNRI',
    'License :: OSI Approved :: Python Software Foundation License': 'Python',
    'License :: OSI Approved :: Qt Public License (QPL)': 'QPL',
    'License :: OSI Approved :: Ricoh Source Code Public License': 'Ricoh Source Code Public License - (BAD)',
    'License :: OSI Approved :: Sleepycat License': 'Sleepycat',
    'License :: OSI Approved :: Sun Industry Standards Source License (SISSL)': 'SISSL',
    'License :: OSI Approved :: Sun Public License': 'SPL',
    'License :: OSI Approved :: University of Illinois/NCSA Open Source License': 'NCSA',
    'License :: OSI Approved :: Vovida Software License 1.0': 'VSL',
    'License :: OSI Approved :: W3C License': 'W3C - not sure',
    'License :: OSI Approved :: X.Net License': 'X.Net License - Deprecated (BAD)',
    'License :: OSI Approved :: zlib/libpng License': 'zlib',
    'License :: OSI Approved :: Zope Public License': 'ZPLv%(TODO: version)s',
    'License :: Other/Proprietary License': 'Proprietary shit - BAD',
    'License :: Public Domain': 'Public Domain',
    'License :: Repoze Public License': 'Repoze Public License - ???'}
