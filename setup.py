#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from pyp2rpm.version import version

from setuptools import setup
from setuptools.command.build_py import build_py as _build_py


description = """Convert Python packages to RPM SPECFILES. The packages can be downloaded from
PyPI and the produced SPEC is in line with Fedora Packaging Guidelines or Mageia Python Policy.

Users can provide their own templates for rendering the package metadata. Both the package
source and metadata can be extracted from PyPI or from local filesystem (local file doesn't
provide that much information though)."""

class build_py(_build_py):
    def run(self):
        # Run the normal build process
        _build_py.run(self)
        # Build test data
        from subprocess import call
        from shutil import copy
        call([sys.executable, 'setup.py', 'sdist'],
             cwd='tests/test_data/utest')
        copy('tests/test_data/utest/dist/utest-0.1.0.tar.gz',
             'tests/test_data/')

setup(
    cmdclass={
        'build_py': build_py,
    },
    name='pyp2rpm',
    version=version,
    description="Convert Python packages to RPM SPECFILES",
    long_description=description,
    keywords='pypi, rpm, spec, specfile, convert',
    author='Bohuslav "Slavek" Kabrda, Robert Kuska, Michal Cyprian, Iryna Shcherbina',
    author_email='bkabrda@redhat.com, rkuska@redhat.com, mcyprian@redhat.com, ishcherb@redhat.com',
    url='https://github.com/fedora-python/pyp2rpm',
    license='MIT',
    packages=['pyp2rpm', 'pyp2rpm.command'],
    package_data={'pyp2rpm': ['templates/*.spec']},
    entry_points={'console_scripts': ['pyp2rpm = pyp2rpm.bin:main']},
    install_requires=['Jinja2',
                      'setuptools',
                      'click',
                      ],
    setup_requires=['setuptools',
                    'flexmock >= 0.9.3',
                    'pytest-runner',
                    'click',
                    'Jinja2',
                    ],
    tests_require=['packaging < 21;python_version<"3.5"', 'pytest < 5;python_version<"3.5"',
                   'pytest < 6.2;python_version=="3.5"', 'pytest;python_version>="3.6"'],
    extras_require={
        'venv metadata': ['virtualenv-api'],
        'sclize': ['spec2scl >= 1.2.0']
    },
    classifiers=['Development Status :: 4 - Beta',
                 'Environment :: Console',
                 'Intended Audience :: Developers',
                 'Intended Audience :: System Administrators',
                 'License :: OSI Approved :: MIT License',
                 'Operating System :: POSIX :: Linux',
                 'Programming Language :: Python',
                 'Programming Language :: Python :: 3',
                 'Topic :: Software Development :: Build Tools',
                 'Topic :: System :: Software Distribution',
                 ]
)
