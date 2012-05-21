from pyp2rpmlib import utils

def for_python_version(name, version):
    return utils.rpm_name(name, version)

__all__ = [for_python_version]
