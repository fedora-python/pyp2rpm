#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pyp2rpm.version import version

from setuptools import setup
from setuptools.command.test import test as TestCommand
import sys

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
    author='Bohuslav "Slavek" Kabrda, Robert Kuska, Michal Cyprian',
    author_email='bkabrda@redhat.com, rkuska@redhat.com, mcyprian@redhat.com',
    url='https://github.com/fedora-python/pyp2rpm',
    license='MIT',
    packages=['pyp2rpm', 'command'],
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
    tests_require=['pytest'],
    extras_require = {
        'venv metadata': ['virtualenv-api'],
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
