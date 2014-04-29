#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pyp2rpm.version import version

from setuptools import setup
from setuptools.command.test import test as TestCommand
import sys


class PyTest(TestCommand):

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = ['tests']
        self.test_suite = True

    def run_tests(self):
        #import here, cause outside the eggs aren't loaded
        import pytest
        errno = pytest.main(self.test_args)
        sys.exit(errno)


description = """Convert Python packages to RPM SPECFILES. The packages can be downloaded from
PyPI and the produced SPEC is in line with Fedora Packaging Guidelines or Mageia Python Policy.

Users can provide their own templates for rendering the package metadata. Both the package
source and metadata can be extracted from PyPI or from local filesystem (local file doesn't
provide that much information though)."""

setup(
    name='pyp2rpm',
    version=version,
    description="Convert Python packages to RPM SPECFILES",
    long_description=description,
    keywords='pypi, rpm, spec, specfile, convert',
    author='Bohuslav "Slavek" Kabrda, Robert Kuska',
    author_email='bkabrda@redhat.com, rkuska@redhat.com',
    url='https://bitbucket.org/bkabrda/pyp2rpm/',
    license='MIT',
    packages=['pyp2rpm', ],
    package_data={'pyp2rpm': ['templates/*.spec']},
    entry_points={'console_scripts': ['pyp2rpm = pyp2rpm.bin:main']},
    install_requires=['Jinja2',
                      'setuptools',
                      ],
    setup_requires=['setuptools',
                    'flexmock >= 0.9.3',
                    'pytest'
                    ],
    cmdclass={'test': PyTest},
    classifiers=['Development Status :: 4 - Beta',
                 'Environment :: Console',
                 'Intended Audience :: Developers',
                 'Intended Audience :: System Administrators',
                 'License :: OSI Approved :: MIT License',
                 'Operating System :: POSIX :: Linux',
                 'Programming Language :: Python',
                 'Topic :: Software Development :: Build Tools',
                 'Topic :: System :: Software Distribution',
                 ]
)
