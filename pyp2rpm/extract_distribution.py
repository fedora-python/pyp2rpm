"""
Modify the Distutils 'bdist_rpm' command (create RPM source and binary
distributions) to be able of automatic rebuild in Fedora's COPR and
fit better to Fedora packaging Guidlines.
"""

import distutils.command.bdist_rpm
import sys
import os.path
import runpy

from distutils.errors import DistutilsOptionError

bdist_rpm_orig = distutils.command.bdist_rpm.bdist_rpm


class extract_distribution(bdist_rpm_orig):
    class_distribution = None

    def finalize_package_data(self):
        """This method is executed before run method. Only distribution attribute is
        stored to class attribute during metadata extraction so all interesting data must
        be added to distribution here.
        """
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

        if self.distribution.metadata.classifiers is None:
            self.distribution.metadata.classifiers = []

    def run(self):
        extract_distribution.class_distribution = self.distribution

    @staticmethod
    def _list(var):
        if var is None:
            return []
        if isinstance(var, str):
            var = var.split('\n')
        elif not isinstance(var, list):
            raise DistutilsOptionError("{} is not a list".format(var))
        return var

# extract_distribution command is executed instead of bdist_rpm thanks to this assignment
distutils.command.bdist_rpm.bdist_rpm = extract_distribution


def run_setup(setup, *args):
    dirname = os.path.dirname(setup)
    filename = os.path.basename(setup)
    if filename.endswith('.py'):
        filename = filename[:-3]
    sys.path.insert(0, dirname)
    sys.argv[1:] = args
    runpy.run_module(filename, run_name='__main__', alter_sys=True)
