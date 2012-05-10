#!/usr/bin/env python

import argparse

parser = argparse.ArgumentParser(description = 'Convert PyPI package to RPM specfile.')
parser.add_argument('-p',
                    required = True,
                    help = 'Either name of the package or url of the archive',
                    metavar = 'PYPI_NAME_OR_URL'
                   )

args = parser.parse_args()
