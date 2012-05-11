#!/usr/bin/env python

import argparse

parser = argparse.ArgumentParser(description = 'Convert PyPI package to RPM specfile.')
parser.add_argument('-p',
                    required = True,
                    help = 'Name of the package on PyPI',
                    metavar = 'PYPI_NAME'
                   )

args = parser.parse_args()
