#!/usr/bin/env python3

from setuptools import setup, find_packages

requirements = ["pyp2rpm~=3.3.1"]

setup(
    name="utest",
    version="0.1.0",
    description="Micro test module",
    license="GPLv2+",
    author="pyp2rpm Developers",
    author_email='bkabrda@redhat.com, rkuska@redhat.com, mcyprian@redhat.com, ishcherb@redhat.com',
    url='https://github.com/fedora-python/pyp2rpm',
    install_requires=requirements,
    include_package_data=True,
    packages=find_packages(exclude=["test"]),
    classifiers=(
        "License :: OSI Approved :: GNU General Public License v2 or later (GPLv2+)",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
    ),
)
