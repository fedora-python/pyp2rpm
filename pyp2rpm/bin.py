import getpass
import logging
import os

from pyp2rpm.convertor import Convertor
from pyp2rpm import settings
from pyp2rpm import utils
from pyp2rpm.logger import (register_file_log_handler,
                            register_console_log_handler)

import click
try:
    from spec2scl.convertor import Convertor as SclConvertor
except ImportError:
    SclConvertor = None
except Exception as err:
    SclConvertor = None
    click.echo('Warning: An unexpected error occured when trying'
               ' to import spec2scl: {}'.format(err))


CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])


class Pyp2rpmCommand(click.Command):
    """Base class for pyp2rpm command.

    Modify the help message for SCL related options,
    to single them out in a separate group.
    """

    def format_options(self, ctx, formatter):
        """Writes SCL related options into the formatter as a separate
        group.
        """
        super(Pyp2rpmCommand, self).format_options(ctx, formatter)
        scl_opts = []
        for param in self.get_params(ctx):
            if isinstance(param, SclizeOption):
                scl_opts.append(param.get_scl_help_record(ctx))

        if scl_opts:
            with formatter.section('SCL related options'):
                formatter.write_dl(scl_opts)


class SclizeOption(click.Option):
    """Base class for SCL related options.

    Provide proper validation and help message formatting.
    """

    def handle_parse_result(self, ctx, opts, args):
        """Validate SCL related options before parsing."""
        if 'sclize' in opts and not SclConvertor:
            raise click.UsageError("Please install spec2scl package to "
                                   "perform SCL-style conversion")
        if self.name in opts and 'sclize' not in opts:
            raise click.UsageError(
                "`--{}` can only be used with --sclize option".format(
                    self.name))

        return super(SclizeOption, self).handle_parse_result(ctx, opts, args)

    def get_help_record(self, ctx):
        """Remove help record, so that it does not appear in Options
        section.
        """
        pass

    def get_scl_help_record(self, ctx):
        """Move help record, so that it appears in SCL options section."""
        return super(SclizeOption, self).get_help_record(ctx)


@click.command(context_settings=CONTEXT_SETTINGS, cls=Pyp2rpmCommand)
@click.option('-t',
              help='Template file (jinja2 format) to render (default: "{0}").'
              'Search order is 1) filesystem, 2) default templates.'.format(
                  settings.DEFAULT_TEMPLATE),
              metavar='TEMPLATE')
@click.option('-o',
              help='Default distro whose conversion rules to use '
              '(default:"{0}"). Default templates have their rules associated '
              'and ignore this.'.format(settings.DEFAULT_DISTRO),
              type=click.Choice(settings.KNOWN_DISTROS),
              default=settings.DEFAULT_DISTRO)
@click.option('-b',
              help='Base Python version to package for (fedora '
              'default: "{0}").'.format(settings.DEFAULT_PYTHON_VERSION),
              default=None,
              metavar='BASE_PYTHON')
@click.option('-p',
              help='Additional Python versions to include in the specfile '
              '(e.g -p2 for python2 subpackage). Can be specified multiple '
              'times. Specify additional version or use -b explicitly to '
              'disable default.',
              default=[],
              multiple=True, metavar='PYTHON_VERSIONS')
@click.option('-s',
              help='Spec file ~/rpmbuild/SPECS/python-package_name.spec will '
              'be created (default: prints spec file to stdout).',
              is_flag=True)
@click.option('--srpm',
              help='When used pyp2rpm will produce srpm instead of printing '
              'specfile into stdout.',
              is_flag=True)
@click.option('--proxy',
              help='Specify proxy in the form proxy.server:port.',
              default=None,
              metavar='PROXY')
@click.option('-r',
              help='Name of rpm package (overrides calculated name).',
              default=None,
              metavar='RPM_NAME')
@click.option('-d',
              help='Specify where to save package file, specfile and '
              'generated SRPM (default: "{0}").'.format(
                  settings.DEFAULT_PKG_SAVE_PATH),
              default=settings.DEFAULT_PKG_SAVE_PATH,
              metavar='SAVE_PATH')
@click.option('-v',
              help='Version of the package to download (ignored for '
              'local files).',
              metavar='VERSION')
@click.option('--prerelease',
              help='Use the latest release, even if it is a pre-release '
              '(default: disabled).',
              is_flag=True)
@click.option('--venv / --no-venv',
              help='Enable / disable metadata extraction from virtualenv '
              '(default: enabled).',
              default=True)
@click.option('--autonc/ --no-autonc',
              help='Enable / disable using automatic provides with '
              'a standardized name in dependencies declaration ('
              'default: disabled).',
              default=None)
@click.option('--sclize',
              help='Convert tags and macro definitions to SCL-style using '
              '`spec2scl` module. NOTE: SCL related options can be provided '
              'alongside this option.',
              is_flag=True)
# SCL related options
@click.option('--no-meta-runtime-dep',
              cls=SclizeOption,
              help='Don\'t add the runtime dependency on the scl '
              'runtime package.',
              is_flag=True)
@click.option('--no-meta-buildtime-dep',
              cls=SclizeOption,
              help='Don\'t add the buildtime dependency on the scl '
              'runtime package.',
              is_flag=True)
@click.option('--skip-functions',
              cls=SclizeOption,
              help='Comma separated list of transformer functions to skip.',
              default='',
              metavar='FUNCTIONS')
@click.option('--no-deps-convert',
              cls=SclizeOption,
              help='Don\'t convert dependency tags (mutually exclusive '
              'with --list-file).',
              is_flag=True)
@click.option('--list-file',
              cls=SclizeOption,
              help='List of the packages/provides, that will be in the SCL '
              '(to convert Requires/BuildRequires properly). Lines in '
              'the file are in form of "pkg-name %%{?custom_prefix}", where '
              'the prefix part is optional.',
              default=None,
              metavar='FILE_NAME')
@click.argument('package', nargs=1)
def main(package, v, prerelease, d, s, r, proxy, srpm, p, b, o, t, venv, autonc,
         sclize, **scl_kwargs):
    """Convert PyPI package to RPM specfile or SRPM.

    \b
    \b\bArguments:
    PACKAGE             Provide PyPI name of the package or path to compressed
                        source file.
    """
    register_file_log_handler('/tmp/pyp2rpm-{0}.log'.format(getpass.getuser()))

    if srpm or s:
        register_console_log_handler()

    distro = o
    if t and os.path.splitext(t)[0] in settings.KNOWN_DISTROS:
        distro = t
    if not distro and not (b or p):
        raise click.UsageError("Default python versions for template {0} are "
                               "missing in settings, add them or use flags "
                               "-b/-p to set python versions.".format(t))

    logger = logging.getLogger(__name__)

    logger.info('Pyp2rpm initialized.')

    convertor = Convertor(package=package,
                          version=v,
                          prerelease=prerelease,
                          save_dir=d,
                          template=t or settings.DEFAULT_TEMPLATE,
                          distro=distro,
                          base_python_version=b,
                          python_versions=p,
                          rpm_name=r,
                          proxy=proxy,
                          venv=venv,
                          autonc=autonc)

    logger.debug(
        'Convertor: {0} created. Trying to convert.'.format(convertor))
    converted = convertor.convert()
    logger.debug('Convertor: {0} succesfully converted.'.format(convertor))

    if sclize:
        converted = convert_to_scl(converted, scl_kwargs)

    if srpm or s:
        if r:
            spec_name = r + '.spec'
        else:
            prefix = 'python-' if not convertor.name.startswith(
                'python-') else ''
            spec_name = prefix + convertor.name + '.spec'
        logger.info('Using name: {0} for specfile.'.format(spec_name))
        if d == settings.DEFAULT_PKG_SAVE_PATH:
            # default save_path is rpmbuild tree so we want to save spec
            # in  rpmbuild/SPECS/
            spec_path = d + '/SPECS/' + spec_name
        else:
            # if user provide save_path then save spec in provided path
            spec_path = d + '/' + spec_name
        spec_dir = os.path.dirname(spec_path)
        if not os.path.exists(spec_dir):
            os.makedirs(spec_dir)
        logger.debug('Opening specfile: {0}.'.format(spec_path))

        if not utils.PY3:
            converted = converted.encode('utf-8')
        with open(spec_path, 'w') as f:
            f.write(converted)
            logger.info('Specfile saved at: {0}.'.format(spec_path))

        if srpm:
            msg = utils.build_srpm(spec_path, d)
            logger.info(msg)

    else:
        logger.debug('Printing specfile to stdout.')
        if utils.PY3:
            print(converted)
        else:
            print(converted.encode('utf-8'))
        logger.debug('Specfile printed.')
    logger.info("That's all folks!")


def convert_to_scl(spec, scl_options):
    """Convert spec into SCL-style spec file using `spec2scl`.

    Args:
        spec: (str) a spec file
        scl_options: (dict) SCL options provided
    Returns:
        A converted spec file
    """
    scl_options['skip_functions'] = scl_options['skip_functions'].split(',')
    scl_options['meta_spec'] = None
    convertor = SclConvertor(options=scl_options)
    return str(convertor.convert(spec))
