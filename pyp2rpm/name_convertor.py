from pyp2rpm import settings


class NameConvertor():

    def __init__(self, distro):
        self.distro = distro

    @staticmethod
    def rpm_versioned_name(name, version):
        """Properly versions the name.
        For example:
        rpm_versioned_name('python-foo', '26') will return python26-foo
        rpm_versioned_name('pyfoo, '3') will return python3-pyfoo

        If version is same as settings.DEFAULT_PYTHON_VERSION, no change is done.

        Args:
            name: name to version
            version: version or None
        Returns:
            Versioned name or the original name if given version is None.
        """
        if version == settings.DEFAULT_PYTHON_VERSION:
            return name

        versioned_name = name
        if version:
            if name.startswith('python-'):
                versioned_name = name.replace(
                    'python-', 'python{0}-'.format(version))
            else:
                versioned_name = 'python{0}-{1}'.format(version, name)

        return versioned_name

    def rpm_name(self, name, python_version=None):
        """Returns name of the package coverted to (possibly) correct package name according to Packaging Guidelines.
        Args:
            name: name to convert
            python_version: python version for which to retrieve the name of the package
        Returns:
            Converted name of the package, that should be in line with Fedora Packaging Guidelines.
            If for_python is not None, the returned name is in form python%(version)s-%(name)s
        """
        rpmized_name = name
        if self.distro == 'mageia':
            exclude_string = 'python-'
        else:
            exclude_string = 'py'

        name = name.replace('.', "-")
        if name.lower().find(exclude_string) == -1:  # name doesn't contain "py" => prefix with "python-"
            rpmized_name = 'python-{0}'.format(name)
        if name.endswith('-python'):  # name ends with "-python" => strip that and put it to front (I hope that's for Mageia, too)
            rpmized_name = 'python-{0}'.format(name.replace('-python', ''))
        # else the name contains "py" as its part => do nothing
        # or the name is in form "python-%(name)s", which is fine, toO
        if self.distro == 'mageia':
            rpmized_name = rpmized_name.lower()
        return NameConvertor.rpm_versioned_name(rpmized_name, python_version)
