from pkg_resources import Requirement

from pyp2rpmlib import utils

class RequirementsParser(object):
    @staticmethod
    def dependency_to_rpm(dep, runtime):
        converted = []
        if len(dep.specs) == 0:
            converted.append(['Requires', utils.rpm_name(dep.project_name)])
        else:
            for ver_spec in dep.specs:
                if ver_spec[0] == '!=':
                    converted.append(['Conflicts', utils.rpm_name(dep.project_name), '=', ver_spec[1]])
                elif ver_spec[0] == '==':
                    converted.append(['Requires', utils.rpm_name(dep.project_name), '=', ver_spec[1]])
                else:
                    converted.append(['Requires', utils.rpm_name(dep.project_name), ver_spec[0], ver_spec[1]])

        if not runtime:
            for conv in converted:
                conv[0] = "Build" + conv[0]

        return converted

    @staticmethod
    def deps_from_setup_py(requires, runtime = True):
        parsed = []

        for req in requires:
            parsed.append(Requirement.parse(req))
        in_rpm_format = []
        for dep in parsed:
            in_rpm_format.extend(RequirementsParser.dependency_to_rpm(dep, runtime))

        return in_rpm_format

