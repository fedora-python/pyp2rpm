class PackageData(object):
    def __init__(self, local_file, name, version):
        self.local_file = local_file
        self.name = name
        self.version = version

    def __getattr__(self, name):
        if name in self.__dict__:
            return self.__dict__[name]

        return 'TODO:'

    @property
    def pkg_name(self, name):
        if self.name.lower().find('py') != -1:
            return self.name
        else:
            return 'python-%s'

class PypiData(PackageData):
    def __init__(self, local_file, name, version, md5, url):
        super(PackageData, self).__init__(local_file, name, version)
        self.md5 = md5
        self.url = url

class LocalData(PackageData):
    def __init__(self, local_file, name, version):
        super(PackageData, self).__init__(local_file, name, version)
