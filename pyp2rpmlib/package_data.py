class PackageData(object):
    def __init__(self, name, version):
        self.name = name
        self.version = version

class PypiData(PackageData):
    def __init__(self, name, version, md5, url):
        super(PackageData, self).__init__(name, version)
        self.md5 = md5
        self.url = url

class LocalData(PackageData):
    def __init__(self, name, version, local_file):
        super(PackageData, self).__init__(name, version)
        self.local_file = local_file
