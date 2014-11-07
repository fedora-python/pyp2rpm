import argparse
import getpass
import logging
import os

from pyp2rpm.convertor import Convertor
from pyp2rpm import settings
from pyp2rpm import utils
from pyp2rpm.logger import register_file_log_handler, register_console_log_handler


def main():

    parser = argparse.ArgumentParser(
        description='Convert PyPI package to RPM specfile.')
    parser.add_argument('-n',
                        required=False,
                        help='Name of the package on PyPI (ignored for local files).',
                        metavar='PYPI_NAME')
    parser.add_argument('-v',
                        required=False,
                        help='Version of the package to download (ignored for local files).',
                        metavar='VERSION')
    parser.add_argument('-m',
                        required=False,
                        help='Where to get metadata from ("pypi" or "local", default: "{0}").'.format(
                            settings.DEFAULT_METADATA_SOURCE),
                        metavar='METADATA_SOURCE',
                        choices=['pypi', 'local'],
                        default=settings.DEFAULT_METADATA_SOURCE)
    parser.add_argument('-s',
                        required=False,
                        help='Where to get package from ("pypi" or "/full/path/to/local/file", default: "{0}").'.format(
                            settings.DEFAULT_PKG_SOURCE),
                        metavar='PACKAGE_SOURCE',
                        default=settings.DEFAULT_PKG_SOURCE)
    parser.add_argument('-d',
                        required=False,
                        help='Specify where to save package file, specfile and generated SRPM (default: "{0}").'.format(
                            settings.DEFAULT_PKG_SAVE_PATH),
                        metavar='SAVE_DIR',
                        default=settings.DEFAULT_PKG_SAVE_PATH)
    parser.add_argument('-r',
                        required=False,
                        help='Name of rpm package (overrides calculated name).',
                        metavar='RPM_NAME',
                        default=None)
    parser.add_argument('-t',
                        required=False,
                        help='Template file (jinja2 format) to render (default: "{0}"). Search order is 1) filesystem, 2) default templates.'.format(
                            settings.DEFAULT_TEMPLATE),
                        metavar='TEMPLATE')  # no default, because we need to know, whether this was specified or not
    parser.add_argument('-o',
                        required=False,
                        help='Default distro whose conversion rules to use (default: "{0}"). Default templates have their rules associated and ignore this.'.format(
                            settings.DEFAULT_DISTRO),
                        metavar='DISTRO',
                        default=settings.DEFAULT_DISTRO,
                        choices=settings.KNOWN_DISTROS)
    parser.add_argument('-b',
                        required=False,
                        help='Base Python version to package for (default: "{0}").'.format(
                            settings.DEFAULT_PYTHON_VERSION),
                        metavar='BASE_PYTHON',
                        default=settings.DEFAULT_PYTHON_VERSION)
    parser.add_argument('-p',
                        required=False,
                        help='Additional Python versions to include in the specfile (e.g -p3 for %%{?with_python3}). Can be specified multiple times.',
                        metavar='PYTHON_VERSION',
                        default=[],
                        action='append')
    parser.add_argument('--srpm',
                        required=False,
                        help='When used pyp2rpm will produce srpm instead of printing specfile into stdout.',
                        action='store_true')
    parser.add_argument('--proxy',
                        required=False,
                        help='Specify proxy in the form proxy.server:port.',
                        metavar='PROXY',
                        default=None)

    register_file_log_handler('/tmp/pyp2rpm-{0}.log'.format(getpass.getuser()))

    args = parser.parse_args()

    if args.srpm:
        register_console_log_handler()

    if args.n is None and not os.path.exists(args.s):
        parser.error(
            'You must specify name of the package (-n) or full path (-s).')

    distro = args.o
    if args.t in settings.KNOWN_DISTROS:
        distro = args.t

    logger = logging.getLogger(__name__)

    logger.info('Pyp2rpm initialized.')

    convertor = Convertor(name=args.n,
                          version=args.v,
                          metadata_from=args.m,
                          source_from=args.s,
                          save_dir=args.d,
                          template=args.t or settings.DEFAULT_TEMPLATE,
                          distro=distro,
                          base_python_version=args.b,
                          python_versions=args.p,
                          rpm_name=args.r,
                          proxy=args.proxy,
                          )

    logger.debug('Convertor: {0} created. Trying to convert.'.format(convertor))
    converted = convertor.convert()
    logger.debug('Convertor: {0} succesfully converted.'.format(convertor))

    if args.srpm:

        if args.r:
            spec_name = args.r + '.spec'
        else:
            spec_name = 'python-' + args.n + '.spec'
        logger.info('Using name: {0} for specfile.'.format(spec_name))
        if args.d == settings.DEFAULT_PKG_SAVE_PATH:
            # default save_path is rpmbuild tree so we want to save spec
            # in  rpmbuild/SPECS/
            spec_path = args.d + '/SPECS/' + spec_name
        else:
            # if user provide save_path then save spec in provided path
            spec_path = args.d + '/' + spec_name
        logger.debug('Opening specfile: {0}.'.format(spec_path))
        with open(spec_path, 'w') as f:
            f.write(converted)
            logger.info('Specfile saved at: {0}.'.format(spec_path))

        msg = utils.build_srpm(spec_path, args.d)
        if utils.PY3:
            logger.info(msg.decode('utf-8'))
        else:
            logger.info(msg)

    else:
        logger.debug('Printing specfile to stdout.')
        if utils.PY3:
            print(converted)
        else:
            print(converted.encode('utf-8'))
        logger.debug('Specfile printed.')
    logger.info("That's all folks!")
