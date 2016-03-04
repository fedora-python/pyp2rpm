"""
Modify the Distutils 'bdist_rpm' command (create RPM source and binary
distributions) to be able of automatic rebuild in Fedora's COPR and
fit better to Fedora packaging Guidlines.
"""

import distutils.command
import distutils.command.bdist_rpm
from distutils.debug import DEBUG
import glob
import re
import time
import pprint
import sys

bdist_rpm_orig = distutils.command.bdist_rpm.bdist_rpm


class bdist_fedora (bdist_rpm_orig):
    def finalize_package_data (self):

        bdist_rpm_orig.finalize_package_data(self)
        self.distribution.force_arch = self.force_arch

        self.distribution.build_requires = self.build_requires or (
                               self._list(getattr(self.distribution, 'setup_requires', []))
                               + self._list(getattr(self.distribution, 'tests_require', [])))

        self.distribution.run_requires = self.requires or self._list(getattr(
            self.distribution, 'install_requires', []))

        self.distribution.conflicts = [dep.replace('!=', '=') 
                                      for dep in self.distribution.run_requires if '!=' in dep]

        if (getattr(self.distribution, 'entry_points', None)
            and 'setuptools' not in self.distribution.run_requires):
            self.distribution.run_requires.append('setuptools')

        self.distribution.distribution_name = self.distribution

        script_options = [ 
            ('prep', 'prep_script'),
            ('build', 'build_script'),
            ('install', 'install_script'),
            ('clean', 'clean_script'),
        ]

        for (rpm_opt, attr) in script_options:
            val = getattr(self, attr, None)
            if val:
                setattr(self.distribution, rpm_opt, val) 

    def run(self):
        __builtins__['distribution'] = self.distribution

    def _get_license(self):
        return self.distribution.get_license()

    @staticmethod
    def _list(var):
        if var is None:
            return []
        elif not isinstance(var, list):
            raise DistutilsOptionError("{} is not a list".format(var))
        return var 

distutils.command.bdist_rpm.bdist_rpm = bdist_fedora

def run_setup(setup, *args):
    import os.path
    import runpy
    import sys
    import pprint

    dirname = os.path.dirname(setup)
    filename = os.path.basename(setup)
    if filename.endswith('.py'):
        filename = filename[:-3]
    sys.path.insert(0, dirname)
    sys.argv[1:] = args
    runpy.run_module(filename, run_name='__main__', alter_sys=True)

