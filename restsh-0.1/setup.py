#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages
import restshlib

setup(
    name = 'restsh',
    version = ":versiontools:restshlib:",
    description = "A simple rest shell client",
    long_description = "",
    keywords = 'rest shell',
    author = 'Jesús Espino García',
    author_email = 'jespinog@gmail.com',
    url = 'https://github.com/jespino/restsh',
    license = 'BSD',
    include_package_data = True,
    packages = ['restshlib', ],
    scripts = ['restsh', ],
    install_requires=[
        'distribute',
        'requests',
    ],
    setup_requires = [
        'versiontools >= 1.8',
    ],
    classifiers = [
        "Programming Language :: Python",
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP',
    ]
)
