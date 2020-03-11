import logging
import re

from pkg_resources import Requirement

from pyp2rpm.dependency_convert import convert_requirement

logger = logging.getLogger(__name__)


def dependency_to_rpm(dep, runtime, use_rich_deps=True):
    """Converts a dependency got by pkg_resources.Requirement.parse()
    to RPM format.
    Args:
        dep - a dependency retrieved by pkg_resources.Requirement.parse()
        runtime - whether the returned dependency should be runtime (True)
        or build time (False)
    Returns:
        List of semi-SPECFILE dependencies (package names are not properly
        converted yet).
        For example: [['Requires', 'jinja2', '{name}'],
                      ['Conflicts', 'jinja2', '{name} = 2.0.1']]
    """
    logger.debug('Dependencies provided: {0} runtime: {1}.'.format(
        dep, runtime))
    converted = convert_requirement(dep, use_rich_deps)

    if not runtime:
        for conv in converted:
            conv[0] = "Build" + conv[0]
    logger.debug('Converted dependencies: {0}.'.format(converted))

    return converted


def deps_from_pyp_format(requires, runtime=True, use_rich_deps=True):
    """Parses dependencies extracted from setup.py.
    Args:
        requires: list of dependencies as written in setup.py of the package.
        runtime: are the dependencies runtime (True) or build time (False)?
    Returns:
        List of semi-SPECFILE dependencies (see dependency_to_rpm for format).
    """
    parsed = []
    logger.debug("Dependencies from setup.py: {0} runtime: {1}.".format(
        requires, runtime))

    for req in requires:
        try:
            parsed.append(Requirement.parse(req))
        except ValueError:
            logger.warn("Unparsable dependency {0}.".format(req),
                        exc_info=True)

    in_rpm_format = []
    for dep in parsed:
        in_rpm_format.extend(dependency_to_rpm(dep, runtime, use_rich_deps))
    logger.debug("Dependencies from setup.py in rpm format: {0}.".format(
        in_rpm_format))

    return in_rpm_format


def deps_from_pydit_json(requires, runtime=True):
    """Parses dependencies returned by pydist.json, since versions
    uses brackets we can't use pkg_resources to parse and we need a separate
    method
    Args:
        requires: list of dependencies as written in pydist.json of the package
        runtime: are the dependencies runtime (True) or build time (False)
    Returns:
        List of semi-SPECFILE dependecies (see dependency_to_rpm for format)
    """
    parsed = []
    for req in requires:
        # req looks like 'some-name (>=X.Y,!=Y.X)' or 'someme-name' where
        # 'some-name' is the name of required package and '(>=X.Y,!=Y.X)'
        # are specs
        name, specs = None, None
        # len(reqs) == 1 if there are not specified versions, 2 otherwise
        reqs = req.split(' ')
        name = reqs[0]
        if len(reqs) == 2:
            specs = reqs[1]
            # try if there are more specs in spec part of the requires
            specs = specs.split(",")
            # strip brackets
            specs = [re.sub('[()]', '', spec) for spec in specs]
            # this will divide (>=0.1.2) to ['>=', '0', '.1.2']
            # or (0.1.2) into ['', '0', '.1.2']
            specs = [re.split('([0-9])', spec, 1) for spec in specs]
            # we have separated specs based on number as delimiter
            # so we need to join it back to rest of version number
            # e.g ['>=', '0', '.1.2'] to ['>=', '0.1.2']
            for spec in specs:
                spec[1:3] = [''.join(spec[1:3])]
        if specs:
            for spec in specs:
                if '!' in spec[0]:
                    parsed.append(['Conflicts', name, '{{name}} = {}'.format(spec[1])])
                elif specs[0] == '==':
                    parsed.append(['Requires', name, '{{name}} = {}'.format(spec[1])])
                else:
                    parsed.append(['Requires', name, '{{name}} {} {}'.format(
                        spec[0], spec[1])])
        else:
            parsed.append(['Requires', name, '{name}'])

    if not runtime:
        for pars in parsed:
            pars[0] = 'Build' + pars[0]

    return parsed
