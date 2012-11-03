from pkg_resources import Requirement

class DependencyParser(object):
    @staticmethod
    def dependency_to_rpm(dep, runtime):
        """Converts a dependency got by pkg_resources.Requirement.parse() to RPM format.
        Args:
            dep - a dependency retrieved by pkg_resources.Requirement.parse()
            runtime - whether the returned dependency should be runtime (True) or build time (False)
        Returns:
            List of semi-SPECFILE dependencies (package names are not properly converted yet).
            For example: [['Requires', 'jinja2'], ['Conflicts', 'jinja2', '=', '2.0.1']]
        """
        converted = []
        if len(dep.specs) == 0:
            converted.append(['Requires', dep.project_name])
        else:
            for ver_spec in dep.specs:
                if ver_spec[0] == '!=':
                    converted.append(['Conflicts', dep.project_name, '=', ver_spec[1]])
                elif ver_spec[0] == '==':
                    converted.append(['Requires', dep.project_name, '=', ver_spec[1]])
                else:
                    converted.append(['Requires', dep.project_name, ver_spec[0], ver_spec[1]])

        if not runtime:
            for conv in converted:
                conv[0] = "Build" + conv[0]

        return converted

    @staticmethod
    def deps_from_pyp_format(requires, runtime = True):
        """Parses dependencies extracted from setup.py.
        Args:
            requires: list of dependencies as written in setup.py of the package.
            runtime: are the dependencies runtime (True) or build time (False)?
        Returns:
            List of semi-SPECFILE dependencies (see dependency_to_rpm for format).
        """
        parsed = []

        for req in requires:
            try:
                parsed.append(Requirement.parse(req))
            except ValueError as e: # TODO: log unparsable dependency
                pass
        in_rpm_format = []
        for dep in parsed:
            in_rpm_format.extend(DependencyParser.dependency_to_rpm(dep, runtime))

        return in_rpm_format

